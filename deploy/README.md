# LungTic 同机多站点部署手册

本方案假设服务器已经运行另一个网站。LungTic 只占用以下资源，不修改另一网站的目录、域名或 systemd 服务：

- 官网：`respulse.top`、`www.respulse.top`
- 管理台：`console.respulse.top`
- 内部 API：`127.0.0.1:9100`
- 程序目录：`/opt/lungtic`
- 数据目录：`/srv/lungtic-data`
- 环境文件：`/etc/lungtic/lungtic.env`

## 权限边界

| 身份 | 用途 | 可以访问 |
| --- | --- | --- |
| `lungtic-app` | FastAPI 与备份任务 | 数据库、上传目录、素材与安装包 |
| `lungtic-deploy` | GitHub Actions 发布 | `/opt/lungtic`，仅可重启 `lungtic-control.service` |
| `www-data` | Nginx | 只读素材和已发布安装包，不能读取数据库、上传分块或环境密钥 |

不要把 `lungtic-deploy` 加入 `lungtic-runtime` 或 `lungtic-web`，也不要把 `www-data` 加入 `lungtic-runtime`。
服务器上已有的 `lungtic` 用户不参与本系统，以下命令不会修改其主组、附加组、家目录或权限。

## 1. 安装依赖

以下命令适用于 Ubuntu/Debian：

```bash
sudo apt update
sudo apt install -y nginx python3 python3-venv python3-pip sqlite3 rsync curl clamav clamav-daemon certbot
```

## 2. 创建隔离账户和目录

以下初始化命令可以重复执行；已经存在的组或账户会被保留，不需要删除后重建：

```bash
getent group lungtic-runtime >/dev/null || sudo groupadd --system lungtic-runtime
getent group lungtic-web >/dev/null || sudo groupadd --system lungtic-web
getent group lungtic-deploy >/dev/null || sudo groupadd --system lungtic-deploy

id -u lungtic-app >/dev/null 2>&1 || sudo useradd --system --gid lungtic-runtime --groups lungtic-web --home-dir /srv/lungtic-data --shell /usr/sbin/nologin lungtic-app
id -u lungtic-deploy >/dev/null 2>&1 || sudo useradd --create-home --gid lungtic-deploy --shell /bin/bash lungtic-deploy

sudo usermod --append --groups lungtic-web lungtic-app
sudo usermod --append --groups lungtic-deploy lungtic-deploy
sudo usermod --append --groups lungtic-web www-data

sudo install -d -o root -g lungtic-deploy -m 2775 /opt/lungtic
sudo install -d -o lungtic-deploy -g lungtic-deploy -m 0755 /opt/lungtic/releases

sudo install -d -o lungtic-app -g lungtic-web -m 0710 /srv/lungtic-data
sudo install -d -o lungtic-app -g lungtic-web -m 2750 /srv/lungtic-data/releases
sudo install -d -o lungtic-app -g lungtic-web -m 2750 /srv/lungtic-data/assets
sudo install -d -o lungtic-app -g lungtic-runtime -m 0750 /srv/lungtic-data/uploads
sudo install -d -o lungtic-app -g lungtic-runtime -m 0750 /srv/lungtic-data/backups

sudo install -d -o root -g lungtic-runtime -m 0750 /etc/lungtic
```

`/srv/lungtic-data` 的组只有穿越权限；Nginx 只能进入 `releases` 和 `assets`，无法列出或读取数据库。

## 3. 配置 ClamAV

在 `/etc/clamav/clamd.conf` 中启用：

```text
TCPSocket 3310
TCPAddr 127.0.0.1
```

然后执行：

```bash
sudo systemctl restart clamav-daemon
sudo systemctl enable clamav-daemon
sudo ss -lntp | grep 3310
```

3310 不得在云安全组或系统防火墙中开放。

## 4. 写入生产环境

先创建生产环境文件，再参考仓库根目录的 `.env.example` 填入飞书 App ID、App Secret、租户、部门、所有者和随机 IP 哈希盐：

```bash
sudo install -d -o root -g lungtic-runtime -m 0750 /etc/lungtic
sudo install -o root -g lungtic-runtime -m 0640 /dev/null /etc/lungtic/lungtic.env
openssl rand -hex 32
sudo nano /etc/lungtic/lungtic.env

sudo chown root:lungtic-runtime /etc/lungtic/lungtic.env
sudo chmod 0640 /etc/lungtic/lungtic.env
```

`openssl` 生成的随机值写入 `LUNGTIC_IP_HASH_SALT`。不要把环境文件内容、飞书 App Secret 或 SSH 私钥发到聊天、工单或 Git。

生产地址必须保持为：

```dotenv
LUNGTIC_PUBLIC_ORIGIN=https://respulse.top
LUNGTIC_ADMIN_ORIGIN=https://console.respulse.top
LUNGTIC_FEISHU_REDIRECT_URI=https://console.respulse.top/auth/feishu/callback
```

飞书开放平台中的重定向 URL 也必须同步改成 `https://console.respulse.top/auth/feishu/callback`。
飞书参数的获取步骤和首次部署清单见仓库根目录的 `DEPLOYMENT.md`。

## 5. 无中断申请 HTTPS 证书

先确认三个域名的 DNS 都指向本服务器。不要停止现有 Nginx；使用独立的 HTTP 引导站点：

```bash
sudo install -d -o root -g root -m 0755 /var/www/letsencrypt
sudo cp deploy/nginx/lungtic-bootstrap.conf /etc/nginx/sites-available/lungtic-bootstrap.conf
sudo ln -s /etc/nginx/sites-available/lungtic-bootstrap.conf /etc/nginx/sites-enabled/lungtic-bootstrap.conf
sudo nginx -t
sudo systemctl reload nginx

sudo certbot certonly --webroot --webroot-path /var/www/letsencrypt -d respulse.top -d www.respulse.top
sudo certbot certonly --webroot --webroot-path /var/www/letsencrypt -d console.respulse.top
```

证书成功后启用正式虚拟主机：

```bash
sudo cp deploy/nginx/lungtic.conf /etc/nginx/sites-available/lungtic.conf
sudo ln -s /etc/nginx/sites-available/lungtic.conf /etc/nginx/sites-enabled/lungtic.conf
sudo unlink /etc/nginx/sites-enabled/lungtic-bootstrap.conf
sudo nginx -t
sudo systemctl reload nginx
```

不要删除或修改另一网站在 `sites-enabled` 中的配置。LungTic 使用独立的 `server_name`、限流区和日志文件。

## 6. 安装 systemd 与最小 sudo 权限

```bash
sudo cp deploy/systemd/lungtic-control.service /etc/systemd/system/
sudo cp deploy/systemd/lungtic-backup.service /etc/systemd/system/
sudo cp deploy/systemd/lungtic-backup.timer /etc/systemd/system/
sudo install -o root -g root -m 0440 deploy/sudoers/lungtic-deploy /etc/sudoers.d/lungtic-deploy
sudo visudo -cf /etc/sudoers.d/lungtic-deploy
sudo systemctl daemon-reload
sudo systemctl enable lungtic-control.service
```

如果 `command -v systemctl` 不是 `/usr/bin/systemctl`，先修改 sudoers 模板中的路径。普通发布不拥有 Nginx reload 权限；Nginx 配置变更只能由服务器管理员执行。

## 7. 配置 GitHub Actions

在 GitHub 仓库的 `production` Environment 中配置：

- `DEPLOY_HOST`：服务器 SSH 地址
- `DEPLOY_USER`：`lungtic-deploy`
- `DEPLOY_SSH_KEY`：仅供该账户使用的 SSH 私钥
- `DEPLOY_KNOWN_HOSTS`：人工核验后的服务器 host key

服务器上的公钥只写入 `/home/lungtic-deploy/.ssh/authorized_keys`。

运行 `Deploy production` 工作流后，构建产物会上传到 `/opt/lungtic/releases/<commit-sha>`。激活脚本会创建版本独立的 Python 环境、原子切换 `/opt/lungtic/current`、重启服务并检查 `127.0.0.1:9100/healthz`；健康检查失败会切回上一版本。

## 8. 启用备份

首次成功发布后：

```bash
sudo systemctl enable --now lungtic-backup.timer
sudo systemctl start lungtic-backup.service
sudo systemctl status lungtic-backup.timer
```

备份保存在 `/srv/lungtic-data/backups`。应另行同步到服务器之外的受控存储。

## 9. 验收

```bash
sudo nginx -t
sudo systemctl status lungtic-control
sudo systemctl status clamav-daemon
curl --fail http://127.0.0.1:9100/healthz
curl -I https://respulse.top
curl -I https://console.respulse.top/auth/feishu/start
sudo ss -lntp | grep 9100
```

9100 必须只监听 `127.0.0.1`。云安全组与系统防火墙只允许必要的 SSH、80 和 443，不开放 9100 或 3310。
