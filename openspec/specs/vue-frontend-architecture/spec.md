# vue-frontend-architecture Specification

## Purpose

本规范定义项目从 Jinja2 模板 + 原生 JS 重构为 Vue 3 SPA 后的前端架构契约。覆盖 SPA 入口、静态资源服务、客户端路由回退、鉴权与 CSRF 流程、HTTPException 状态码保留、多阶段 Docker / PyInstaller / Python 直跑三种部署形态下的 dist 解析。

实现见 `web/` 与 `outlook_web/segments/00_spa_serve.py` + `outlook_web/segments/11_routes_spa_catchall.py`。

## Requirements

### Requirement: SPA shell serving with template fallback
系统 SHALL 在 Vue SPA 构建产物存在时返回 SPA shell，否则透明回退到现有 Jinja 模板，且无需运维干预。

#### Scenario: 返回 SPA shell
- **WHEN** `web/dist/index.html` 存在，已登录用户请求 `/`
- **THEN** 系统 SHALL 返回 `web/dist/index.html` 的内容，content-type 为 `text/html`。

#### Scenario: 回退到 Jinja 模板
- **WHEN** `web/dist/index.html` 不存在，已登录用户请求 `/`
- **THEN** 系统 SHALL 渲染 `templates/index.html` 并附带 `app_version`、`changelog_url` 上下文。

#### Scenario: 未登录访问首页
- **WHEN** 未登录用户请求 `/`
- **THEN** 系统 SHALL 重定向到 `/login`，行为与 `@login_required` 一致。

### Requirement: SPA static asset hosting
系统 SHALL 通过 `/assets/<path:filename>` 暴露 Vite 输出的带 hash 的静态资源，并阻止越级访问。

#### Scenario: 命中存在的资源
- **WHEN** 浏览器请求 `/assets/index-<hash>.js`，且文件位于 `web/dist/assets/` 下
- **THEN** 系统 SHALL 通过 `send_from_directory` 返回该文件的字节内容，且响应 status 为 200。

#### Scenario: 缺失资源
- **WHEN** 请求的 `/assets/<filename>` 不存在
- **THEN** 系统 SHALL 返回 404，且 SHALL NOT 返回 SPA shell。

#### Scenario: 路径越级
- **WHEN** 请求路径在解析后会指向 `web/dist/assets/` 之外
- **THEN** 系统 SHALL 返回 403。

#### Scenario: SPA 未构建
- **WHEN** `web/dist/` 不存在，任何 `/assets/<filename>` 请求到达
- **THEN** 系统 SHALL 返回 404。

### Requirement: SPA client-side route fallback
系统 SHALL 把所有非 `/api/*`、非 `/static/*`、未被业务路由捕获的路径，统一返回 SPA shell，让 Vue Router 接管前端路由。

#### Scenario: 直接访问 Vue 路由
- **WHEN** 浏览器请求 `/some/vue/route`（不是已注册的 API 路由）且 SPA 已构建
- **THEN** 系统 SHALL 返回 `web/dist/index.html`，content-type 为 `text/html`，status 为 200。

#### Scenario: 显式拒绝 `/api/<unknown>`
- **WHEN** 浏览器请求 `/api/nonexistent-path`，且没有任何 API 处理器匹配
- **THEN** 系统 SHALL 返回 404，且 SHALL NOT 返回 SPA shell。

#### Scenario: 显式拒绝 `/static/*`
- **WHEN** 浏览器请求 `/static/<anything>`，但该静态文件不存在
- **THEN** 系统 SHALL 返回 404，且 SHALL NOT 返回 SPA shell。

#### Scenario: SPA 未构建时的未知路径
- **WHEN** `web/dist/` 不存在，浏览器请求未注册的 `/some/route`
- **THEN** 系统 SHALL 返回 404，且 SHALL NOT 渲染旧 Jinja 模板。

### Requirement: HTTPException status preservation
系统 SHALL 在全局异常处理器中保留 `werkzeug.exceptions.HTTPException` 的原始状态码与描述，不再统一转成 500。

#### Scenario: `abort(404)` 透传
- **WHEN** 业务路由调用 `abort(404)`，或 Flask 路由系统抛出 NotFound
- **THEN** 全局 `errorhandler(Exception)` SHALL 检测 `isinstance(HTTPException)`，并返回原始 `error.code`（即 404）与原始描述。

#### Scenario: 非 HTTP 异常仍按 500 处理
- **WHEN** 业务代码抛出非 HTTPException 的异常
- **THEN** 系统 SHALL 返回 500，并把 `str(error)` 作为 JSON `error` 字段。

### Requirement: Single-origin auth via Flask session
系统 SHALL 在 Vue SPA 形态下继续使用 Flask session cookie + Flask-WTF CSRF 鉴权，不引入跨域、不切换到 JWT。

#### Scenario: 登录写入 session
- **WHEN** 用户向 `/login` POST 正确密码
- **THEN** 系统 SHALL 设置 `session['logged_in'] = True` 并返回 `{success: true}`，不返回任何 token。

#### Scenario: CSRF token 拉取
- **WHEN** 已登录前端调用 `GET /api/csrf-token`
- **THEN** 系统 SHALL 返回 `{csrf_token, csrf_disabled}`；该路由 SHALL `@csrf_exempt` 且 `@login_required`，并附 `Cache-Control: no-store`。

#### Scenario: 未登录 API 调用
- **WHEN** 未登录的请求命中带 `@login_required` 的 `/api/*` 路由
- **THEN** 系统 SHALL 返回 401 JSON `{success: false, error, need_login: true}`，前端 SHALL 触发跳转到 `/login`。

#### Scenario: CSRF 失效透明重试
- **WHEN** 前端收到 400 或 403 + 响应体包含 `csrf` 关键字
- **THEN** axios 拦截器 SHALL 清空缓存的 CSRF token、重新拉取、用新 token 重发原始请求一次；该重试 SHALL NOT 再次触发同样的重试循环。

### Requirement: Multi-stage Docker build
系统 SHALL 通过多阶段 Dockerfile 在镜像里同时构建前端与运行后端，且不需要宿主机预装 node。

#### Scenario: Stage 1 构建前端
- **WHEN** `docker build` 进入第一阶段
- **THEN** 镜像 SHALL 基于 `node:20-alpine`，执行 `npm install --no-audit --no-fund` 与 `npm run build`，生成 `/web/dist/`。

#### Scenario: Stage 2 运行后端
- **WHEN** `docker build` 进入第二阶段
- **THEN** 镜像 SHALL 基于 `python:3.11-slim`，安装 `requirements.txt + gunicorn`，并把 stage 1 的 `/web/dist/` 拷贝到 `/app/web/dist/`。

#### Scenario: 单 worker 不可改
- **WHEN** 容器启动
- **THEN** 启动命令 SHALL 使用 `gunicorn -k gthread -w 1 --threads ${GUNICORN_THREADS:-4}`，且 SHALL NOT 提供调高 worker 数的环境变量。

### Requirement: Frozen-bundle SPA resolution
系统 SHALL 在 PyInstaller frozen 状态、Docker 状态、Python 直跑状态下都能正确解析 `web/dist/` 路径，且支持环境变量覆盖。

#### Scenario: 环境变量覆盖
- **WHEN** 环境变量 `WEB_DIST_DIR` 已设置
- **THEN** 系统 SHALL 使用该路径作为 `WEB_DIST_DIR`，忽略默认探测逻辑。

#### Scenario: PyInstaller frozen
- **WHEN** `sys.frozen=True`
- **THEN** 系统 SHALL 通过 `resource_path('web', 'dist')` 经由 `sys._MEIPASS` 解析路径。

#### Scenario: Python 直跑或 Docker
- **WHEN** `sys.frozen=False`
- **THEN** 系统 SHALL 解析为项目根目录下的 `web/dist/`。
