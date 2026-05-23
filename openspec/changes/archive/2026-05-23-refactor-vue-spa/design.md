## 背景

旧前端通过 `render_template('index.html')` + 全局 JS 渲染。新前端在 `web/` 下用 Vite 构建为静态产物。两套形态需要在同一个 Flask 进程里共存一段时间：dev-vue 分支默认走 SPA，旧 dev 分支或 SPA 未构建时仍可回退到 Jinja。

## 目标 / 非目标

**目标：**

- 保留 `/api/*` 路由与对外 API 兼容契约（包括 SSE 流式接口）。
- `/`、`/login`、`/logout` 在构建产物存在时透明切换到 SPA，不存在时无人介入即可回退。
- 浏览器直接访问 `/some/vue/route`（如 `/internal-eml`）也能返回 SPA shell，由 Vue Router 接管前端路由。
- `/assets/*` 直接命中 Vite 输出（带 hash 的文件名），与旧的 `/assets/index.css` 拼接路由互斥。
- 同源部署（Flask serve dist + API），不引入 CORS。
- Docker、Windows EXE、Python 直跑三种部署形态都能交付前端产物。

**非目标：**

- 不暴露 Vite dev server 到生产部署。
- 不改写已有 `/api/*` 路由的响应字段或行为。
- 不为前端建立独立的 token-based 鉴权（继续使用 Flask session cookie + CSRF）。

## 设计决策

### 用专用 segment 承载 SPA 服务

新增 `00_spa_serve.py`（在 `01_bootstrap.py` 之后加载）和 `11_routes_spa_catchall.py`（最末加载）。前者集中暴露 `WEB_DIST_DIR` / `has_spa_build()` / `_serve_spa_or_fallback()`，后者注册 `/assets/<path>` 与 `/<path:path>` 两条 catch-all。

原因：把 SPA 关注点抽到独立段，避免污染 segment 04 的业务路由；catch-all 必须最后注册，否则会优先匹配掉之后注册的 API 路由。

备选方案：在 `04_routes_groups_accounts.py` 内联。被否决：跨业务关注点混合不利于审阅，也让"SPA 关掉"或"换部署形态"的回滚面变大。

### Catch-all 显式拒绝 `/api/` 与 `/static/`

`spa_catch_all(path)` 显式 `abort(404)` 当 path 以 `api/` 或 `static/` 开头。这样即使 SPA shell 加载、API 路由名打错时，调用方拿到的还是 404 而不是 SPA HTML（避免 health check 误判为成功）。

### 全局错误处理器保留 HTTPException 状态码

旧的 `@app.errorhandler(Exception)` 把所有异常都返回 500。SPA catch-all 里用 `abort(404)` 会被这个处理器吃成 500。新增 `isinstance(error, HTTPException)` 分支保留原始 code 与 description。

### 优雅回退到旧模板

`_serve_spa_or_fallback(template_name, context=None)` 先检查 `WEB_DIST_INDEX.is_file()`，没有就走 `render_template`。回退路径下仍能登录、查看邮箱，给 SPA 出问题的环境留一条退路。

### 鉴权与 CSRF

继续用 Flask session cookie + Flask-WTF CSRF：

- `POST /login` 与 `GET /api/csrf-token` 维持原契约（前者 `@csrf_exempt`，后者也 `@csrf_exempt` 但 `@login_required`）。
- 前端 axios 拦截器在 `POST/PUT/DELETE/PATCH` 之前透明拉取并附加 `X-CSRFToken` 头。
- CSRF token 失效（400/403 + 响应体含 `csrf`）触发一次透明重试。
- 401 触发 `window.location.href = '/login'`，避免登录页自身递归。

### SPA 资源路径

Vite 默认 `base: '/'`，输出 `dist/index.html` + `dist/assets/index-<hash>.{js,css}`。Flask catch-all 把 `/assets/<filename>` 直接 `send_from_directory(WEB_DIST_ASSETS, filename)`，并做路径解析校验阻止越级访问。

### 部署形态

- **Docker**：多阶段，stage 1 `node:20-alpine` 跑 `npm install && npm run build`；stage 2 `python:3.11-slim` 复制 dist 到 `/app/web/dist`。镜像保持单 worker gunicorn。
- **Windows EXE**：`outlookEmail.spec` 在 `web/dist` 存在时把它加入 `datas`，PyInstaller 把产物嵌入单文件。运行时 `_resolve_web_dist()` 用 `sys._MEIPASS` 或环境变量 `WEB_DIST_DIR` 解析路径。
- **Python 直跑**：开发期 `cd web && npm run dev` 起 Vite 5173，proxy 把 `/api` 转 :5000；生产 `npm run build` 后 Flask 直接 serve dist。

## 风险 / 权衡

- 前端构建依赖 node：CI 增加 `setup-node` 步骤；ARM 镜像 + Apple Silicon 已验证。
- 单 worker 约束仍然成立：Token 刷新 SSE 任务用进程内 dict 维护状态。Docker compose 不允许 `workers > 1`。
- Vue 端体积：主 bundle ~480KB / gzip 150KB，echarts 等懒加载块各 50–170KB。可接受。
- 双轨期 `templates/index.html` 仍依赖被删除的 `bundled_index_css`：本次同步修复 Jinja 直接引用 `static/css/index/*.css` 8 个文件，回退路径不再 500。

## 迁移计划

1. dev-vue 分支合并到 dev 之后立即可用：未构建 `web/dist` 时自动回退旧模板，回滚成本=0。
2. 第二阶段（用户完整回归测试后）删除 `templates/index.html` + `static/js/index/` + `static/css/index/`。
3. PyInstaller spec 条件打包，本地未 `npm build` 时 exe 体积不变。

## 待确认问题

- 是否需要把 SPA 静态资源放到 CDN 或 Nginx 直接 serve，减少 Flask 上下文交换？短期不需要；如果未来出现性能瓶颈再做。
- 是否需要替代 Flask session 为 JWT？同源同端口下不需要。
