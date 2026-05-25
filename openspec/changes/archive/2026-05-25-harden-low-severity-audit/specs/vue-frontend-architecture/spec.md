## MODIFIED Requirements

### Requirement: Single-origin auth via Flask session
系统 SHALL 在 Vue SPA 形态下继续使用 Flask session cookie + Flask-WTF CSRF 鉴权，不引入跨域、不切换到 JWT；并 SHALL 通过 POST 才执行登出操作，避免跨站 GET 触发的 CSRF DoS。

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

#### Scenario: POST 才能登出
- **WHEN** 已登录用户向 `/logout` 发起 POST 请求并附带有效 CSRF token
- **THEN** 系统 SHALL `session.pop('logged_in')` 并返回 `{success: true}`。

#### Scenario: GET 不改变 session
- **WHEN** 浏览器以 GET 方式访问 `/logout`（包括跨站 `<img src="/logout">` / `<a href="/logout">` 等场景）
- **THEN** 系统 SHALL NOT 修改 session，且 SHALL 返回 SPA shell（让 Vue Router 把用户引到登录页或合适的视图）。

#### Scenario: 缺失 CSRF token 的 POST 失败
- **WHEN** 向 `/logout` 发起 POST 但未携带 X-CSRFToken 头
- **THEN** 系统 SHALL 返回 400 并保留当前 session，不执行任何 session.pop。
