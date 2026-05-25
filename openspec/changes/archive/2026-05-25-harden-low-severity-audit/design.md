## 背景

前一次审计发现的 3 个低优先级问题都属于"默认不安全"类硬化项：单独看影响有限，组合在错误配置或恶意页面下会放大。本次集中修复并写入契约，避免回归。

## 目标 / 非目标

**目标：**

- 让内网 EML 协议客户端在 HTTPS 部署下默认启用证书校验。
- 给 audit-logs 关键词过滤一个稳定、可解释的语义（不出现 SQL 通配符渗漏）。
- 关闭 GET 触发的 logout，避免 `<img src="/logout">` 类 CSRF DoS。

**非目标：**

- 不修改 HTTP 部署的现有行为（默认 baseURL 仍是 http://，跳过 verify 是 noop）。
- 不为前端登出引入新的 token；继续走 session cookie + CSRF。
- 不调整 audit-logs 的字段或权限模型。

## 设计决策

### TLS verify 三态而非布尔

`InternalEmlClient.__init__` 接受 `verify_tls: Optional[bool] = None`：

- `None`（默认）：按 `base_url.scheme` 推断 — `http` 时 `verify=False`（noop，跳过 urllib3 警告），`https` 时 `verify=True`。
- `True` / `False`：显式覆盖。

`_build_client_for_account()` 读取环境变量 `INTERNAL_EML_INSECURE` —— 配置为 truthy 时传 `verify_tls=False`，否则传 `None` 让 client 自动判断。

原因：保留对内网自签证书的逃生通道，又让默认行为安全。环境变量是部署级开关，比账号级配置更合适（这是基础设施特征，不是单账号偏好）。

备选：直接强制 `verify=True`。被否决：现网内网部署可能用自签证书，硬开会让"按域名自动路由 baseURL"在第一次升级后立刻失联。

### LIKE 转义用反斜杠 + 显式 ESCAPE

```python
def _escape_like(value: str) -> str:
    return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')

like = f'%{_escape_like(keyword)}%'
# SQL: ... LIKE ? ESCAPE '\\'
```

SQLite 默认 LIKE 不支持转义；必须显式声明 `ESCAPE '\\'`。`\\` 必须先转义自身，否则用户输入 `\` 后会污染下一个字符。

原因：用户可能想搜诸如 `100%` 这样字面字符，转义后仍能命中；同时关闭通过 `%` 让 LIKE 退化成全表扫描的渠道。

### Logout 改为 POST-only + GET 仅展示

原 `/logout` 同时接受 GET / POST 并都 `session.pop`。改成：

- `GET /logout`：返回 SPA shell（或 fallback 模板），**不修改 session**。访问 `/logout` URL 的用户依然能看到登录页（Vue 路由跳转），但跨站 `<img>` 无法触发登出。
- `POST /logout`：CSRF 校验通过后 `session.pop` 并返回 `{success: true}`。

前端 `authApi.logout()` 由 GET 改为 POST，axios 拦截器自动附加 X-CSRFToken 头。

原因：CSRF token 只对状态变更请求有意义。把"清 session"绑定到 POST 而不是 GET 是 HTTP 语义本身的要求（GET 必须幂等无副作用）。

备选：在 GET /logout 路径上加 Origin / Referer 检查。被否决：浏览器在某些场景（PWA、扩展、`Referrer-Policy`）下不发 Referer；维护白名单成本高，且违反"GET 不应有副作用"的 HTTP 契约。

## 风险 / 权衡

- TLS 默认开启后，已部署的 HTTPS 自签内网用户在升级后会"突然连不上"。缓解：环境变量 `INTERNAL_EML_INSECURE=true` 提供 escape hatch，并在 `docs/deploy-mac-lan.md` 注明。
- LIKE 转义会让 `\` 在搜索词中变成转义符；用户搜文件路径里的 `\` 需要输双反斜杠。但 audit-logs 的内容主要是路径分隔符 `/`，对中文用户影响极小。
- Logout 改 POST 会让任何手写脚本（curl GET /logout）不再实际登出；脚本需改用 POST + CSRF。这是预期行为变化，文档中说明。

## 迁移计划

1. 实施时先发 change（active），然后改代码、加测试。
2. 通过本机 e2e 验证后归档（move 到 `openspec/changes/archive/2026-05-25-harden-low-severity-audit/`），把 modifications 合并到 `openspec/specs/`。
3. 回滚：删除新增的环境变量逻辑 + 还原 GET /logout 行为 + 还原 LIKE 拼接。无 schema 变化。

## 待确认问题

- 是否要把 `INTERNAL_EML_INSECURE` 默认值改成 `true`（保留旧行为）？倾向 `false`（safe by default）。
- audit-logs 是否要支持精确匹配（不带通配符）作为可选模式？短期不做；当前转义已经让 `100%` 类查询正常工作。
