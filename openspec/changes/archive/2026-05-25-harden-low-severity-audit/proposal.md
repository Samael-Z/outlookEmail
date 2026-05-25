## 背景与动机

dev-vue 分支自审计共发现 15 个真实问题。修复时优先处理了严重度 🔴 / 🟠 共 12 个，剩下 3 个 🟡 低优先级在归档前未动：

- **#11 TLS verify 硬编码 False**：`InternalEmlClient` 三个 HTTP 调用都不校验证书，即使 baseURL 改成 `https://...` 也无效，给内网 HTTPS 部署留下 MITM 面。
- **#12 audit-logs LIKE 通配符未转义**：`GET /api/audit-logs` 的 keyword 参数直接拼到 `LIKE '%kw%'`，用户可传 `%` / `_` 使过滤完全失效。
- **#14 `GET /logout` CSRF DoS**：`/logout` 接受 GET 且会 `session.pop('logged_in')`，第三方页 `<img src="/logout">` 可在 SameSite=Lax 默认下让已登录管理员被强制下线。

修复这三项，并通过 OpenSpec 工作流（active → archive）记录该变更，作为对前一次"跳过 OpenSpec"的补偿。

## 变更内容

- `InternalEmlClient` 增加 `verify_tls` 字段，默认按 baseURL scheme 决定（http=skip、https=verify）；环境变量 `INTERNAL_EML_INSECURE=true` 允许显式跳过验证（用于自签证书）。
- `GET /api/audit-logs` 的 keyword 在拼入 LIKE 前转义 `%`、`_`、`\` 三个字符，并在 SQL 中加 `ESCAPE '\\'` 子句。
- `/logout` 改为 POST-only 修改 session：GET 仅返回 SPA shell（不再 `session.pop`）；前端 `authApi.logout()` 改为 POST，触发 CSRF 校验。

## 能力范围

### 新增能力

- 无（全部修改既有契约）。

### 修改能力

- `internal-eml-mail`：协议客户端 TLS 校验行为可控。
- `vue-frontend-architecture`：登出语义由 GET 改为 POST-only，避免跨站 CSRF。
- `audit-logs`（隐式新建）：审计日志查询的关键词转义契约。

## 影响范围

- 后端：`outlook_web/segments/10_routes_internal_eml.py`（TLS verify）、`outlook_web/segments/09_routes_system_update.py`（LIKE 转义）、`outlook_web/segments/04_routes_groups_accounts.py`（logout 改 POST-only）。
- 前端：`web/src/service/api/auth.ts`（`logout` 改 POST）。
- 测试：新增 `_is_empty` 与 `_extract_filename` 之外的协议客户端 TLS 行为断言；audit-logs LIKE 转义断言。
- OpenSpec：新增 `openspec/specs/audit-logs/spec.md`，修改 `internal-eml-mail` 与 `vue-frontend-architecture`。

## 非目标

- 不重构 audit-logs 端点的字段结构。
- 不修改 SameSite cookie 策略（保留 Lax）。
- 不引入 nginx / 反代层的额外 Origin 检查（在应用层完成）。
