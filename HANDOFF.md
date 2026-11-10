# 朗泰 LungTic 宣传网站交接文档

交接日期：2026-11-10

整理目录：`xuan_web`

上游基线：`WangZX-07/LungTic-Website` 的 `d4632d6`

## 1. 项目定位

本仓库是朗泰 LungTic 的完整宣传网站与运营后台，包含：

- 面向公众的品牌官网；
- 飞书企业自建应用登录的管理台；
- 结构化 CMS、安装包版本管理、上传扫描和下载统计；
- FastAPI 控制服务；
- Nginx、systemd、备份与 GitHub Actions 部署配置；
- 已审核的桌面端、移动端和管理台设计稿。

官网只宣传已核验能力，不公开模型参数、训练超参数、服务器密钥、默认账号或未经验证的临床效果。公开下载仅面向可独立运行的 TICI Viewer。

## 2. 当前状态

- 品牌名：朗泰 LungTic。
- 官网域名：`respulse.top`，`www.respulse.top` 跳转到主域名。
- 管理台域名：`console.respulse.top`。
- `admin.respulse.top` 已被其他系统使用，本项目不得占用。
- 内部 API：`127.0.0.1:9100`，不得对公网开放。
- ICP 备案号：`辽ICP备2026005104号-2`，页脚链接到工信部备案查询网站。
- 官网与管理台 UI 已审核通过。
- 默认数据和设计稿中的影像均为明确标注的合成数据或真实软件界面，不使用生成式 CT 冒充产品结果。

## 3. 技术架构

| 模块 | 目录 | 技术 |
| --- | --- | --- |
| 公共官网 | `apps/public-web` | Vue 3、Vite、TypeScript |
| 管理控制台 | `apps/admin-web` | Vue 3、Vite、TypeScript |
| 控制服务 | `server` | FastAPI、SQLAlchemy、SQLite WAL |
| 部署与运维 | `deploy` | Nginx、systemd、ClamAV、Shell |
| 端到端测试 | `tests/e2e` | Playwright |
| 设计验收资料 | `design-review`、`DESIGN.md` | 已审核稿与实现截图 |

公开官网从 `/api/public/*` 获取已发布内容和下载版本；接口不可用时回退到前端内置的最后有效内容。管理台通过同域反向代理访问 `/api/admin/*` 和 `/auth/*`。

## 4. 权限边界

服务器使用三个隔离身份：

| 身份 | 职责 |
| --- | --- |
| `lungtic-app` | 运行 FastAPI 和备份任务，访问数据库、上传目录、素材和安装包 |
| `lungtic-deploy` | 接收 GitHub Actions 发布，只能写 `/opt/lungtic` 并重启 `lungtic-control.service` |
| `www-data` | Nginx，只读公开素材与已发布安装包 |

服务器上原有的 `lungtic` 用户不参与本项目，不应修改其主组、家目录或权限。普通发布账户没有 Nginx 重载权限，避免影响同机的另一网站。

## 5. 本地开发

### 前端

```bash
npm ci
npm run dev:public
npm run dev:admin
```

默认开发地址由各 Vite 配置决定。公共官网和管理台应分别启动。

### 后端

Windows：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".\server[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir server --host 127.0.0.1 --port 9100
```

Linux/macOS：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e "./server[dev]"
.venv/bin/python -m uvicorn app.main:app --app-dir server --host 127.0.0.1 --port 9100
```

本地环境复制 `.env.example` 为 `.env`，生产环境使用 `/etc/lungtic/lungtic.env`。仓库没有默认账号、默认密钥或绕过飞书登录的生产入口。

## 6. 验证命令

```bash
npm run typecheck
npm run build
npm run test:e2e
python -m pytest server
```

交接时应至少确认：

- 前后端类型检查和构建通过；
- 后端测试通过；
- Playwright 桌面、手机、平板和宽屏用例通过；
- `git diff --check` 无错误；
- 仓库中不存在 `.env`、私钥、数据库、安装包或上传数据。

## 7. 飞书配置

生产环境必须配置：

```dotenv
LUNGTIC_FEISHU_APP_ID=cli_xxx
LUNGTIC_FEISHU_APP_SECRET=xxx
LUNGTIC_FEISHU_ALLOWED_TENANT_KEYS=xxx
LUNGTIC_FEISHU_ALLOWED_DEPARTMENT_IDS=od-xxx
LUNGTIC_FEISHU_OWNER_OPEN_IDS=ou_xxx
LUNGTIC_FEISHU_REDIRECT_URI=https://console.respulse.top/auth/feishu/callback
```

获取位置：

1. App ID、App Secret：飞书开放平台 → 企业自建应用 → 凭证与基础信息。
2. Tenant Key：API 调试台执行“获取企业信息”。
3. 部门 ID：API 调试台执行“搜索部门”，选择 `open_department_id`，复制 `od-` 开头的值。
4. 所有者 Open ID：通过手机号或邮箱获取用户 ID，选择 `open_id`，复制 `ou_` 开头的值。
5. 在安全设置中添加准确的生产回调地址，并发布应用版本、完成管理员审批。

App Secret 只保存在服务器环境文件或 GitHub Secret 中，不得写入仓库、工单、截图或聊天记录。

## 8. 不进入 Git 的数据

以下内容必须保存在服务器数据目录或受控备份中：

- `/etc/lungtic/lungtic.env`；
- SQLite 数据库及 WAL 文件；
- CMS 图片与优化版本；
- 上传分块与临时文件；
- 发布安装包；
- SSH 私钥与飞书 App Secret；
- 备份文件。

`.gitignore` 已覆盖这些常见路径和扩展名，但提交前仍需人工复核。

## 9. 交接清单

- [ ] DNS 已指向目标服务器。
- [ ] `respulse.top`、`www.respulse.top`、`console.respulse.top` 的 HTTPS 证书可用。
- [ ] 飞书应用已发布并审批，回调地址正确。
- [ ] 飞书租户、部门和所有者 ID 已写入生产环境文件。
- [ ] ClamAV 只监听 `127.0.0.1:3310`。
- [ ] FastAPI 只监听 `127.0.0.1:9100`。
- [ ] Nginx 配置未覆盖同机其他网站。
- [ ] GitHub production Environment 的部署密钥已配置。
- [ ] 数据库与素材备份可恢复。
- [ ] 医学宣传文案已完成最终人工核验。
- [ ] 上线后检查 ICP 链接、下载 Range 请求和版本回滚。

## 10. 文档入口

- 快速说明：`README.md`
- 部署总清单：`DEPLOYMENT.md`
- 服务器详细操作：`deploy/README.md`
- 产品边界：`PRODUCT.md`
- 设计规范：`DESIGN.md`
- 第三方许可：`THIRD_PARTY_NOTICES.md`
