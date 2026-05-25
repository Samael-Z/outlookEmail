## 1. InternalEmlClient TLS verify

- [ ] 1.1 给 `InternalEmlClient.__init__` 增加 `verify_tls: Optional[bool] = None`。
- [ ] 1.2 内部计算 `effective_verify`：scheme=http → False，scheme=https + `verify_tls=None` → True，否则用显式值。
- [ ] 1.3 三个请求方法（`get_email`、`download_next`、`delete`）改用 `effective_verify` 替代硬编码 False。
- [ ] 1.4 `_build_client_for_account` 读取环境变量 `INTERNAL_EML_INSECURE`：truthy 时传 `verify_tls=False`，否则传 `None`。

## 2. audit-logs LIKE 转义

- [ ] 2.1 新增 `_escape_sql_like(value)` 工具函数：依次替换 `\` → `\\`、`%` → `\%`、`_` → `\_`。
- [ ] 2.2 `api_get_audit_logs` 关键词构建：`like = f'%{_escape_sql_like(keyword)}%'`。
- [ ] 2.3 SQL 中追加 `ESCAPE '\\'`：`details LIKE ? ESCAPE '\\' OR resource_id LIKE ? ESCAPE '\\' OR user_ip LIKE ? ESCAPE '\\'`。

## 3. Logout POST-only

- [ ] 3.1 `outlook_web/segments/04_routes_groups_accounts.py::logout`：仅在 `request.method == 'POST'` 时 `session.pop('logged_in')`，GET 仅返回 SPA shell（不再 pop）。
- [ ] 3.2 GET 响应仍为 SPA HTML（让 Vue Router 把用户带去 `/login`）。
- [ ] 3.3 前端 `web/src/service/api/auth.ts::authApi.logout` 由 `method: 'GET'` 改为 `method: 'POST'`，axios 拦截器自动附加 CSRF。

## 4. 测试

- [ ] 4.1 单元：`InternalEmlClient(base_url='https://internal/', verify_tls=None)` 应在请求时使用 `verify=True`；`base_url='http://internal/'` 应 `verify=False`；`verify_tls=False` 显式 override。
- [ ] 4.2 单元：`_escape_sql_like('%admin%')` 返回 `'\\%admin\\%'`；`'\\path\\'` 返回 `'\\\\path\\\\'`。
- [ ] 4.3 集成：往 audit_logs 插入两行（details='密码 100% 强度'、details='other'），keyword=`100%%` 命中 1 行；keyword=`100%` 转义后仅命中第一行（精确字面）。
- [ ] 4.4 集成：GET /logout 不修改 session（先登录后访问 GET /logout，再访问 /api/groups 仍能拿到结果）；POST /logout（带 CSRF）后 session 被清空。

## 5. OpenSpec 归档

- [ ] 5.1 移动 `openspec/changes/harden-low-severity-audit/` 到 `openspec/changes/archive/2026-05-25-harden-low-severity-audit/`。
- [ ] 5.2 把 `internal-eml-mail` 修改后的 Scenario 合并进 `openspec/specs/internal-eml-mail/spec.md`。
- [ ] 5.3 把 `vue-frontend-architecture` 修改后的 Scenario 合并进 `openspec/specs/vue-frontend-architecture/spec.md`。
- [ ] 5.4 新增 `openspec/specs/audit-logs/spec.md`。

## 6. 登录页重做（同一批次顺手）

- [ ] 6.1 `web/src/views/_builtin/login/index.vue` 改为全屏（100vh）双栏布局：左品牌渐变区 + 右白色表单卡。
- [ ] 6.2 左侧加 logo + 标语 + feature 列表，背景紫蓝渐变 + 浮动装饰几何形状（CSS only，无外部 SVG）。
- [ ] 6.3 右侧表单卡放大、加阴影；保留密码输入 + 登录按钮 + "默认 admin123 请尽快修改"提示。
- [ ] 6.4 适配深色模式：右侧表单卡背景在 dark 模式下使用深底；左侧渐变保持不变。
- [ ] 6.5 适配窄屏（<= 768px）：单栏布局，品牌区收缩为顶部 banner。
