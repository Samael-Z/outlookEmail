# audit-logs Specification

## Purpose

本规范定义审计日志查询端点的查询契约，重点是 SQL LIKE 通配符的安全处理。`audit_logs` 表由 `01_bootstrap.py` 在 `init_db()` 时创建，由 `log_audit()` 在多个操作点写入；查询端点位于 `09_routes_system_update.py::api_get_audit_logs`。

## Requirements

### Requirement: Audit log query with safe LIKE filtering
系统 SHALL 提供受登录鉴权保护的审计日志查询端点，并在关键词过滤时对 SQL LIKE 通配符做转义，避免用户输入退化整张表扫描或绕过过滤。

#### Scenario: 关键词字面匹配
- **WHEN** 已登录用户请求 `GET /api/audit-logs?keyword=admin`
- **THEN** 系统 SHALL 使用 `details LIKE '%admin%' ESCAPE '\\'`（同时对 resource_id、user_ip 三列做 OR），返回所有 details/resource_id/user_ip 任一列包含字符串 `admin` 的行。

#### Scenario: 关键词包含 LIKE 通配符
- **WHEN** 已登录用户请求 `GET /api/audit-logs?keyword=100%25`（URL 解码后是 `100%`）
- **THEN** 系统 SHALL 在拼入 LIKE 前把 `%` 转义为 `\%`，并在 SQL 中带 `ESCAPE '\\'`；查询 SHALL 仅命中含有字面字符 `100%` 的行，SHALL NOT 命中所有以 `100` 开头的行。

#### Scenario: 关键词包含下划线
- **WHEN** 已登录用户请求 `GET /api/audit-logs?keyword=a_b`
- **THEN** 系统 SHALL 把 `_` 转义为 `\_`，仅匹配字面 `a_b`，SHALL NOT 把 `_` 当作单字符占位通配符。

#### Scenario: 关键词包含反斜杠
- **WHEN** 关键词原始字符串含有 `\`
- **THEN** 系统 SHALL 在转义 `%` / `_` 之前先把 `\` 替换为 `\\`，确保转义字符自身被正确表达。

#### Scenario: 分页参数
- **WHEN** 请求附带 `page` 和 `per_page`
- **THEN** 系统 SHALL 强制 `1 ≤ page` 与 `1 ≤ per_page ≤ 200`，并在响应中返回 `total / page / per_page / logs`。

#### Scenario: 过滤动作与资源类型
- **WHEN** 请求附带 `action` 或 `resource_type` 参数
- **THEN** 系统 SHALL 在查询中添加对应的等值匹配条件，且响应 SHALL 包含 `distinct_actions` 和 `distinct_resource_types` 数组，供前端 dropdown 使用。
