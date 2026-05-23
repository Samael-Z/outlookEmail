## 背景

参考实现来自项目主人提供的 Go SDK（`E:\dextern\workspace\vibecoding\kiroRE\eml\sdk\client.go`）：

- 协议：三个 HTTP GET 端点（download / get / delete），所有响应都用 `Content-Disposition: attachment; filename=<name>` 表达文件名。
- 鉴权：`signature = md5(timestamp + privateKey + suffix)`，其中 suffix 因端点而异（download 为空、get 为邮箱地址、delete 为文件名）。
- "无邮件"信号：响应体是字面量 `b"EMPTY"`（可能带尾部空白）。
- 消费模式：服务端不维护"已读"概念，只能 download / get → 客户端解析 → delete。

## 目标 / 非目标

**目标：**

- 把内网 EML 协议封装为 Python 客户端，行为与 Go SDK 一致。
- 把 internal_eml 当作一类邮箱账号纳入现有 `accounts` 表，与其他类型共享分组 / 标签 / 状态 / 备注语义。
- 落库后立即调用服务端 `/delete`，避免占用内网服务器硬盘。
- 支持随机生成邮箱名（无需用户先注册），适合"一次性收码"场景。
- 让现有"按服务商分组"的邮箱视图不再展示 internal_eml（避免与专用页面重复）。

**非目标：**

- 不直接把内网 EML 邮件透传到对外 API Key 接口。
- 不写 / 不发邮件（项目本身就是只读的邮件管理工具）。
- 不为内网邮件做转发或 WebDAV 备份（数据本身就是消费即删的临时邮件）。

## 设计决策

### 复用 `accounts` 表 + 字段借用

不为内网邮箱新建独立的账号表，而是复用现有 `accounts`：

- `account_type='internal_eml'`、`provider='internal_eml'`
- `imap_host` 借字段存 baseURL（如 `http://mail.jokerque.com:8080`）
- `imap_password` 借字段存 api_key（经 `encrypt_data` 加密，与其他敏感字段一致）
- `client_id`、`refresh_token`、`password` 留空

原因：现有 UI、批量操作、分组、标签、状态、转发开关、导出都已经围绕 `accounts` 表运转。新表会引入大量重复逻辑或多张表 join。借字段需要在所有 switch on account_type 的代码点显式增加分支，但变更面是收敛的。

备选方案：新建 `internal_eml_accounts` 独立表。被否决：会让账号列表 / 编辑抽屉 / 导出 / 标签 / 分组所有现有页面都需要联表查询或额外渲染逻辑。

### 域名 → baseURL 路由表

内置常量 `INTERNAL_EML_DOMAIN_BASEURL_DEFAULT`：

```python
{
    'cs2jp.com': 'http://cs-email-manager.17usoft.com',
    'jokerque.com': 'http://mail.jokerque.com:8080',
}
```

环境变量可覆盖：`INTERNAL_EML_<DOMAIN_UPPER_DOT_TO_UNDERSCORE>_BASEURL`，例如 `INTERNAL_EML_JOKERQUE_COM_BASEURL=http://...`。`INTERNAL_EML_API_KEY` 覆盖默认 `eml_server_private_KEY_2023`。

`_build_client_for_account` 先读 `account.imap_host`，为空时按域名查表。这样既能让账号自带 baseURL（导入时显式提供），也能在域名匹配时复用默认值。

### Consume-and-delete 安全顺序

`fetch_and_store_internal_eml` 的循环顺序严格保证：

1. `client.get_email(addr)` 拿到 (content, filename)。
2. `parse_eml_bytes(content)` 解析为 dict。
3. `INSERT INTO internal_eml_messages (...)` 落库并 `conn.commit()`。
4. 上一步 commit 成功后才调 `client.delete(filename)`。
5. delete 失败时 `continue`（不再 break），继续 drain 队列尾部。

原因：落库失败时绝不能删除服务端文件，否则丢邮件。delete 失败不致命：唯一索引 `(account_id, server_filename)` 保证下一轮重复 fetch 时 `INSERT OR IGNORE` 跳过，不会污染本地数据。

### `_is_empty` 严格匹配

服务端返回 `b"EMPTY"` 时停止 drain。判断条件为 `body.strip() == b"EMPTY"`（精确匹配，忽略尾部空白），而不是 `body[:5] == b"EMPTY"` 这种 prefix 匹配 — 后者会把任何以 "EMPTY" 字节序列开头的真实 EML 误判为空队列。

### `_extract_filename` 支持 RFC 5987

`Content-Disposition` 兼容三种形式：

- `filename="foo.eml"`
- `filename=foo.eml`
- `filename*=UTF-8''<percent-encoded>` (RFC 5987，优先采用)

实现：正则提取 + `urllib.parse.unquote` 按指定 charset 解码。Go SDK 当前只发第一种，前向兼容未来升级。

### 随机邮箱生成端点

`POST /api/internal-eml/accounts/generate-random`：

- 输入：`{ domain?, prefix_length?=10, group_id?, remark? }`
- 用 `secrets.choice` 从 `[a-z0-9]` 池生成前缀，与域名拼接成完整邮箱
- 检查邮箱不重复（最多重试 5 次）
- INSERT 时 `imap_password` 用 `encrypt_data(default_key)` 加密
- 返回新创建账号的 `id` 与完整邮箱地址

前端 `/internal-eml` 页面顶级 🎲 按钮 + dropdown 选域名，前缀长度对用户不可见（固定 10）。

### internal_eml 在邮箱视图中显式过滤

`/mailbox` 页面的左栏（按服务商分类）显式排除 `internal_eml` 类型：

- `loadAccounts` 中 `filter(a => a.account_type !== 'internal_eml')`
- `PROVIDER_CATEGORIES` 不包含 internal_eml 项

原因：内网邮箱有专用 `/internal-eml` 页面（含本地消费的邮件列表、附件下载等定制 UI），主邮箱视图聚焦日常邮箱。

### account_type 在更新路径上的保留

`api_update_account` 与 `api_update_account_v2` 都增加 `is_internal_eml = account_type == 'internal_eml' or provider == 'internal_eml'` 分支：

- 不调用 `get_provider_meta` 的 imap 归一化（否则会变成 `provider='custom'`）
- 不强制写 IMAP_SERVER_NEW / IMAP_PORT
- 保留前端提交的 `imap_host`（baseURL）与 `imap_password`（已加密的 api_key）
- 清空 `client_id`、`refresh_token`、`password`、`imap_port=0`

这是审计发现 + 修复的关键缺陷：忽略此分支会导致编辑账号后 internal_eml 类型被悄悄改成 imap/custom，`/api/internal-eml/<id>/*` 返回 404，并触发转发调度器以空 Graph 凭据轮询。

### 转发调度排除 internal_eml

调度 SQL 加 `AND account_type != 'internal_eml'`：

- internal_eml 没有 client_id / refresh_token，不能调 Graph
- 没有标准 IMAP 端口，也不能走 IMAP 链路
- 转发语义对消费即删的临时邮件意义不大；如未来确实需要，会做独立链路

## 风险 / 权衡

- **HTTP 明文**：内网协议本身没有 HTTPS，`requests.get(verify=False)` 即使指向 HTTPS 也会跳过证书校验。仅在受信任的内网使用。Spec 仍标记为后续工作项。
- **`imap_password` 字段语义模糊**：借字段而非新字段。文档与 spec 都明确"`account_type='internal_eml'` 时 `imap_password` 存的是 api_key"。
- **唯一索引依赖服务端 filename 稳定**：服务端若改名规则会导致重复入库。当前 Go SDK 行为稳定。
- **EML 解析炸弹**：用户控制的发件人可发恶意 multipart 引发解析 OOM；目前用 stdlib BytesParser + `try/except`，最坏情况是 worker OOM 重启。后续可加入大小限制。

## 迁移计划

- 新增表 `internal_eml_messages` 用 `CREATE TABLE IF NOT EXISTS`，对老 SQLite 文件无破坏。
- `accounts` 表不需要 ALTER（所有借字段都已存在）。
- 回滚：删除 segment 10 + 删 `internal_eml_messages` 表 + `accounts` 里把 internal_eml 行删掉即可。

## 待确认问题

- 是否需要把内网邮箱接入对外 API Key？短期不需要，未来按需。
- 是否需要"只读模式"端点（拉取但不删服务端文件）？目前消费即删能满足所有已知场景。
- 是否需要本地保留期清理（例如本地落库 90 天后自动删 `internal_eml_messages`）？暂不实现。
