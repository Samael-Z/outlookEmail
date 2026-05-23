## 背景与动机

项目原有前端是 Jinja2 模板 + 10 个原生 JS 文件 + 8 个分段 CSS（约 6000 行 HTML/JS/CSS）。随着账号管理、临时邮箱、转发、WebDAV、Token 刷新、Cloudflare 等能力陆续加入，单体 `index.html` + 全局变量风格已成为维护瓶颈：

- 没有路由，所有视图通过弹窗叠加，状态依赖全局 DOM
- 没有类型系统，重命名后端字段会在多个 JS 文件里悄悄失同步
- 视觉风格难以统一升级
- 无法承载下一步要做的内网 EML 邮件视图与项目管理（Projects）等新页面

## 变更内容

把前端整体重构为 Vue 3 SPA：

- 在仓库根新增 `web/` 目录，承载基于 Vue 3 + Vite 8 + TypeScript 6 + Naive UI 2.44 + UnoCSS + Pinia 3 + vue-router + vue-i18n 11 的前端工程
- 在 `outlook_web/segments/` 新增三个段：
  - `00_spa_serve.py` 提供 `web/dist/` 路径解析与 `_serve_spa_or_fallback()` 工具函数
  - `11_routes_spa_catchall.py` 在 `/assets/<path>` 暴露 Vite 资源，并通过 `/<path:path>` 让所有非 `/api/*` 路由回到 SPA shell
- 把 `/login` GET、`/` 和 `/logout` GET 改为优先返回 Vue dist，没有构建产物时回退到旧 Jinja 模板
- 单段错误处理器升级：HTTPException 保留原始状态码，不再被错误地包装为 500
- 重构 `Dockerfile` 为多阶段（node:20-alpine 构建前端，python:3.11-slim 承载 Flask + dist）
- `release.yml` 在 PyInstaller 步骤前加入 `setup-node` + `npm run build`
- `outlookEmail.spec` 条件性地把 `web/dist/` 加入 PyInstaller datas
- 11 个业务页面在 Vue 端重写：登录、仪表盘、邮箱视图、账号管理、内网邮箱、临时邮箱、Token 刷新、邮件转发、转发历史、WebDAV、标签、项目、审计日志、Docker 在线更新、系统设置

## 能力范围

### 新增能力

- `vue-frontend-architecture`：Vue 3 SPA 入口、SPA serve + 回退、SPA 资源服务、HTTPException 状态码保留

### 修改能力

- `spa-or-template-serve`（隐式）：`/login` / `/` / `/logout` 改为优先 SPA，不存在时回退旧模板

## 影响范围

- 后端入口与段加载：`web_outlook_app.py` 的 `SEGMENT_FILES` 在 `01_bootstrap.py` 之后新增 `00_spa_serve.py`，并把 `11_routes_spa_catchall.py` 放在最末
- 改造段：`outlook_web/segments/04_routes_groups_accounts.py`（`/login`、`/logout`、`/`、删除 `bundled_index_css`）、`08_forwarding_scheduler_errors.py`（HTTPException 直通）
- 构建链路：`Dockerfile`、`.dockerignore`、`.github/workflows/release.yml`、`outlookEmail.spec`
- 测试：`tests/test_imap_folder_resolution.py` 的 `AssetRenderingTests` 改为校验 SPA shell 与 catch-all
- 文档：新增 `docs/REFACTOR_PLAN_VUE.md`、`docs/deploy-mac-lan.md`；`README.md` 顶部增加 dev-vue 提示

## 非目标

- 不替换 SQLite 或后端 Flask 框架
- 不引入前后端分离的独立部署形态（同源同端口，由 Flask 一并 serve）
- 不删除 `templates/` 与 `static/`（保留为回退路径直到完整回归测试通过）
