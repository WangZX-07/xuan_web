# 朗泰 LungTic 生产部署清单

本文件用于首次部署和交接验收。完整命令与权限说明见 [deploy/README.md](deploy/README.md)。

## 1. 目标拓扑

| 服务 | 地址 | 是否公网开放 |
| --- | --- | --- |
| 公共官网 | `https://respulse.top` | 是 |
| 官网别名 | `https://www.respulse.top` | 仅跳转 |
| 管理台 | `https://console.respulse.top` | 是，必须飞书登录 |
| FastAPI | `127.0.0.1:9100` | 否 |
| ClamAV | `127.0.0.1:3310` | 否 |

同机已有其他网站时，不修改其 Nginx 文件、目录、日志、systemd 服务或域名。`admin.respulse.top` 不属于本项目。

## 2. 部署前检查

- Ubuntu/Debian 服务器可以使用 `sudo`。
- DNS 的三个记录已指向服务器。
- 云安全组和主机防火墙只开放必要的 SSH、80、443。
- 服务器至少保留 2 GiB 可用空间；正式安装包另行估算。
- GitHub 仓库中没有生产密钥。
- 飞书企业自建应用已经创建。

## 3. 安装依赖

```bash
sudo apt update
sudo apt install -y nginx python3 python3-venv python3-pip sqlite3 rsync curl clamav clamav-daemon certbot
```

## 4. 创建隔离账户与目录

以下命令可以重复执行：

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

不要删除已经存在的 `lungtic-runtime`、`lungtic-web`、`lungtic-deploy` 组或账户。

## 5. 配置 ClamAV

编辑 `/etc/clamav/clamd.conf`，确保存在：

```text
TCPSocket 3310
TCPAddr 127.0.0.1
```

```bash
sudo systemctl enable --now clamav-daemon
sudo systemctl restart clamav-daemon
sudo ss -lntp | grep ':3310'
```

输出必须为 `127.0.0.1:3310`，不能是 `0.0.0.0:3310`。

## 6. 创建生产环境文件

先创建文件，再设置内容；不要对尚不存在的文件执行 `chown`：

```bash
sudo install -d -o root -g lungtic-runtime -m 0750 /etc/lungtic
sudo install -o root -g lungtic-runtime -m 0640 /dev/null /etc/lungtic/lungtic.env
openssl rand -hex 32
sudo nano /etc/lungtic/lungtic.env
```

以仓库中的 `.env.example` 为模板。将 `openssl` 输出写入 `LUNGTIC_IP_HASH_SALT`，并填入真实飞书配置。必须保持：

```dotenv
LUNGTIC_ENVIRONMENT=production
LUNGTIC_HOST=127.0.0.1
LUNGTIC_PORT=9100
LUNGTIC_PUBLIC_ORIGIN=https://respulse.top
LUNGTIC_ADMIN_ORIGIN=https://console.respulse.top
LUNGTIC_FEISHU_REDIRECT_URI=https://console.respulse.top/auth/feishu/callback
```

验证权限：

```bash
sudo chown root:lungtic-runtime /etc/lungtic/lungtic.env
sudo chmod 0640 /etc/lungtic/lungtic.env
sudo stat -c '%U %G %a %n' /etc/lungtic/lungtic.env
```

期望结果为 `root lungtic-runtime 640`。不要输出或粘贴环境文件内容。

## 7. 配置飞书

1. 创建企业自建应用。
2. 在“凭证与基础信息”获取 App ID 与 App Secret。
3. 申请用户基本信息、用户组织架构、用户 ID 和部门基础信息的只读权限。
4. 将应用可见范围和通讯录数据权限限制到指定部门。
5. 在安全设置添加 `https://console.respulse.top/auth/feishu/callback`。
6. 创建版本、提交发布并由企业管理员审批。
7. 用 API 调试台获取 Tenant Key、`od-` 开头的部门 ID 和 `ou_` 开头的所有者 Open ID。

## 8. 申请证书并启用 Nginx

先启用 HTTP 引导配置，避免停止同机 Nginx：

```bash
sudo install -d -o root -g root -m 0755 /var/www/letsencrypt
sudo cp deploy/nginx/lungtic-bootstrap.conf /etc/nginx/sites-available/lungtic-bootstrap.conf
sudo ln -sfn /etc/nginx/sites-available/lungtic-bootstrap.conf /etc/nginx/sites-enabled/lungtic-bootstrap.conf
sudo nginx -t
sudo systemctl reload nginx

sudo certbot certonly --webroot --webroot-path /var/www/letsencrypt -d respulse.top -d www.respulse.top
sudo certbot certonly --webroot --webroot-path /var/www/letsencrypt -d console.respulse.top
```

证书成功后：

```bash
sudo cp deploy/nginx/lungtic.conf /etc/nginx/sites-available/lungtic.conf
sudo ln -sfn /etc/nginx/sites-available/lungtic.conf /etc/nginx/sites-enabled/lungtic.conf
sudo unlink /etc/nginx/sites-enabled/lungtic-bootstrap.conf
sudo nginx -t
sudo systemctl reload nginx
```

## 9. 安装 systemd 与最小 sudo 权限

```bash
sudo cp deploy/systemd/lungtic-control.service /etc/systemd/system/
sudo cp deploy/systemd/lungtic-backup.service /etc/systemd/system/
sudo cp deploy/systemd/lungtic-backup.timer /etc/systemd/system/
sudo install -o root -g root -m 0440 deploy/sudoers/lungtic-deploy /etc/sudoers.d/lungtic-deploy
sudo visudo -cf /etc/sudoers.d/lungtic-deploy
sudo systemctl daemon-reload
sudo systemctl enable lungtic-control.service
```

首次发布前服务没有 `/opt/lungtic/current`，此时只启用、不启动。

## 10. 配置 GitHub Actions

在 GitHub 仓库的 `production` Environment 中添加：

| Secret | 值 |
| --- | --- |
| `DEPLOY_HOST` | 服务器 SSH 地址 |
| `DEPLOY_USER` | `lungtic-deploy` |
| `DEPLOY_SSH_KEY` | 该部署账户的专用 SSH 私钥 |
| `DEPLOY_KNOWN_HOSTS` | 人工核验后的服务器 Host Key |

公钥只写入 `/home/lungtic-deploy/.ssh/authorized_keys`。运行 `Deploy production` 工作流后，发布脚本会原子切换版本并执行健康检查；失败时自动恢复上一版本。

## 11. 启用备份

首次发布成功后：

```bash
sudo systemctl enable --now lungtic-backup.timer
sudo systemctl start lungtic-backup.service
sudo systemctl status lungtic-backup.timer --no-pager
```

备份还应同步到服务器之外的受控存储，并实际演练恢复。

## 12. 上线验收

```bash
sudo nginx -t
sudo systemctl status lungtic-control --no-pager
sudo systemctl status clamav-daemon --no-pager
curl --fail http://127.0.0.1:9100/healthz
curl -I https://respulse.top
curl -I https://console.respulse.top/auth/feishu/start
sudo ss -lntp | grep ':9100'
```

必须确认：

- `9100` 和 `3310` 仅监听回环地址；
- 官网显示 `辽ICP备2026005104号-2` 并链接工信部备案查询网站；
- 飞书非指定租户和非指定部门无法登录；
- 官网下载支持 Range 请求；
- 当前版本切换、回滚、备份和恢复均完成验证。
