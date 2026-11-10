# 朗泰 LungTic 官网、CMS 与版本管理平台

这是朗泰 LungTic 宣传官网的独立交接仓库，包含公共官网、飞书登录管理台、结构化 CMS、安装包版本管理和生产部署配置。

## 文档入口

- [HANDOFF.md](HANDOFF.md)：项目背景、架构、权限、飞书配置与完整交接清单。
- [DEPLOYMENT.md](DEPLOYMENT.md)：首次生产部署的顺序化操作清单。
- [deploy/README.md](deploy/README.md)：同机多站点的详细服务器部署手册。
- [PRODUCT.md](PRODUCT.md)：宣传内容与产品事实边界。
- [DESIGN.md](DESIGN.md)：已审核的 UI 与交互规范。

## 项目组成

| 目录 | 内容 |
| --- | --- |
| `apps/public-web` | Vue 3 / Vite / TypeScript 公共官网 |
| `apps/admin-web` | CMS、安装包发布和运维管理台 |
| `server` | FastAPI、SQLAlchemy、SQLite WAL、飞书 OAuth 与 ClamAV |
| `deploy` | Nginx、systemd、备份、原子发布和最小 sudo 权限 |
| `tests/e2e` | Playwright 响应式与可访问性测试 |
| `design-review` | 已审核设计稿与实现截图 |

## 生产地址

- 官网：`https://respulse.top`
- 官网别名：`https://www.respulse.top`
- 管理台：`https://console.respulse.top`
- 内部 API：`127.0.0.1:9100`
- ICP：`辽ICP备2026005104号-2`

`admin.respulse.top` 属于其他系统，本项目不会使用。

## 本地开发

```bash
npm ci
npm run dev:public
npm run dev:admin
```

后端：

```bash
python -m venv .venv
python -m pip install -e "./server[dev]"
python -m uvicorn app.main:app --app-dir server --host 127.0.0.1 --port 9100
```

复制 `.env.example` 为本地 `.env` 后填写飞书测试应用配置。生产环境使用 `/etc/lungtic/lungtic.env`，不要把真实密钥写进仓库。

## 验证

```bash
npm run typecheck
npm run build
npm run test:e2e
python -m pytest server
```

## 安全边界

- 没有默认账号、默认密钥或生产登录绕过入口。
- 安装包、SQLite、CMS 素材、上传分块、备份与密钥不进入 Git。
- FastAPI 和 ClamAV 只监听回环地址。
- 普通发布账户不能重载 Nginx，避免影响同机其他网站。
- 官网不展示模型参数、训练超参数或未经验证的性能与临床效果。
- 本项目是科研原型和辅助决策工具，不替代医生，不得直接用于患者治疗决策。
