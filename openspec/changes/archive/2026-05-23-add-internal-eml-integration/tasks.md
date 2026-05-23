## 1. 协议客户端

- [x] 1.1 `InternalEmlClient` 类：`base_url`、`private_key`、可选 `proxies`、`timeout=30`。
- [x] 1.2 `_sign(suffix)` 生成 `timestamp`（Unix 秒字符串）与 `md5(timestamp + private_key + suffix)` hex。
- [x] 1.3 `_is_empty(body)` 用 `body.strip() == b"EMPTY"` 精确匹配。
- [x] 1.4 `get_email(email_addr)` → `(content, filename, error?)`，无邮件时返回 `(None, None, None)`。
- [x] 1.5 `download_next()` → `(content, filename, error?)`。
- [x] 1.6 `delete(filename)` → `(ok: bool, error?: str)`。
- [x] 1.7 `_extract_filename(content_disposition)`：优先 `filename*=<charset>'<lang>'<percent-encoded>`（RFC 5987）→ `filename="..."` → `filename=...`。

## 2. EML 解析

- [x] 2.1 `parse_eml_bytes(content)` 使用 stdlib `BytesParser` + `policy.default`，返回 `{subject, from, to, date, text, html, attachments[]}`。
- [x] 2.2 解析异常以最小副作用兜底（不抛出，返回部分字段）。

## 3. 数据库层

- [x] 3.1 新表 `internal_eml_messages`：`id` PK、`account_id` FK、`email`、`server_filename`、`subject`、`from_addr`、`to_addr`、`body_text`、`body_html`、`has_attachment`、`raw_eml` BLOB、`received_at`、`fetched_at`、`is_read`。
- [x] 3.2 唯一索引 `(account_id, server_filename)` 防重复入库。
- [x] 3.3 索引 `(account_id, received_at DESC)` 加速列表查询。
- [x] 3.4 `ensure_internal_eml_schema()` 在 segment 加载时执行（CREATE TABLE IF NOT EXISTS）。

## 4. 域名 → baseURL 路由

- [x] 4.1 内置 `INTERNAL_EML_DOMAIN_BASEURL_DEFAULT = {'cs2jp.com': '...', 'jokerque.com': '...'}`。
- [x] 4.2 `get_internal_eml_baseurl_for_domain(domain)` 先查环境变量 `INTERNAL_EML_<DOMAIN>_BASEURL`，再查内置表。
- [x] 4.3 `get_internal_eml_default_key()` 先查 `INTERNAL_EML_API_KEY`，再用内置默认值。
- [x] 4.4 `_build_client_for_account(account)`：先用 `account.imap_host`，为空时按域名查表；解密 `account.imap_password` 作为 `private_key`；附加分组级 proxy_url。

## 5. 账号 CRUD 端点

- [x] 5.1 `POST /api/internal-eml/accounts`（单个创建）：email 必填、可选 api_key/base_url；`encrypt_data(api_key)` 后 INSERT。
- [x] 5.2 `POST /api/internal-eml/accounts/bulk`（批量）：每行 `email[----api_key[----base_url]]`，返回 created / skipped 列表与各自原因。
- [x] 5.3 `POST /api/internal-eml/accounts/generate-random`：domain 可选（缺省随机挑选）、prefix_length 默认 10、最多重试 5 次直到不冲突。
- [x] 5.4 `GET /api/internal-eml/config/domains`：返回当前可用域名与默认 key。

## 6. 邮件消费端点

- [x] 6.1 `POST /api/internal-eml/<account_id>/refresh` 触发 `fetch_and_store_internal_eml(account)`：单账号单次最多 drain 200 封。
- [x] 6.2 `GET /api/internal-eml/<account_id>/messages` 支持分页 / keyword 模糊（主题 / 发件人 / 正文）。
- [x] 6.3 `GET /api/internal-eml/<account_id>/messages/<msg_id>` 返回详情；自动把 `is_read` 置为 1；附带按 `iter_attachments()` 解析的附件元数据。
- [x] 6.4 `DELETE /api/internal-eml/<account_id>/messages/<msg_id>` 删除本地行（不再调服务端 — 服务端在 fetch 时已删）。
- [x] 6.5 `GET /api/internal-eml/<account_id>/messages/<msg_id>/attachments/<att_idx>` 直接从 `raw_eml` 解码返回附件二进制。

## 7. Consume-and-delete 安全循环

- [x] 7.1 落库 commit 成功后才调 `client.delete`。
- [x] 7.2 单次 delete 失败 `continue`（不再 break），错误累计到 `error` 字符串。
- [x] 7.3 `INSERT OR IGNORE` 配合唯一索引，保证未删除文件下一轮重复 fetch 时不会重复入库。
- [x] 7.4 EML 解析失败时 break（异常路径，不继续 drain）。

## 8. account_type 在更新路径上的保留

- [x] 8.1 `04_routes_groups_accounts.py::api_update_account` 增加 `is_internal_eml` 分支。
- [x] 8.2 `08_forwarding_scheduler_errors.py::api_update_account_v2` 增加同样的分支（注意此处实际是 `app.view_functions['api_update_account']` 的覆盖目标）。
- [x] 8.3 两个分支都：保留 `account_type='internal_eml'` / `provider='internal_eml'`、清空 `client_id`/`refresh_token`/`password`、`imap_port=0`、保留前端提交的 `imap_host` 与 `imap_password`。

## 9. 转发调度

- [x] 9.1 `08_forwarding_scheduler_errors.py` 调度 SQL 加 `AND account_type != 'internal_eml'`。
- [x] 9.2 注释说明：内网邮箱不走 IMAP / Graph 转发，避免空凭据刷屏。

## 10. 段加载

- [x] 10.1 `web_outlook_app.py::SEGMENT_FILES` 在 `09_routes_system_update.py` 之后加入 `10_routes_internal_eml.py`。
- [x] 10.2 段加载顺序在 `00_spa_serve` 与 `11_routes_spa_catchall` 之间，确保 API 路由先注册。

## 11. 前端 service 层

- [x] 11.1 `web/src/service/api/internal-eml.ts`：`getDomains`、`createAccount`、`bulkCreate`、`generateRandom`、`refresh`、`list`、`detail`、`remove`、`attachmentUrl`。
- [x] 11.2 数据类型 `InternalEmlMessage`、`InternalEmlMessageDetail`、`InternalEmlAttachment`、`DomainsConfig`、`CreateAccountPayload`、`BulkCreateItem`。

## 12. 前端页面

- [x] 12.1 `/internal-eml` 页面：三栏（账号 / 邮件 / 详情），顶部 🎲 随机生成按钮 + 添加按钮。
- [x] 12.2 🎲 随机按钮带 dropdown 选域名（前缀长度对用户不可见，固定 10）。
- [x] 12.3 账号列表项末尾增加复制邮箱按钮、删除按钮。
- [x] 12.4 邮件列表支持分页、关键词搜索；详情含发件人 / 收件人 / 时间 / 附件 / HTML（经 DOMPurify 净化）。
- [x] 12.5 内网 EML 在导入对话框（账号管理页）也作为 tab 之一（单个 / 批量两种模式）。

## 13. 邮箱视图过滤

- [x] 13.1 `/mailbox` 页 `loadAccounts` 排除 `account_type === 'internal_eml'`。
- [x] 13.2 `PROVIDER_CATEGORIES` 数组移除 internal_eml 项。

## 14. 文档

- [x] 14.1 `docs/REFACTOR_PLAN_VUE.md` 第四节描述 internal_eml 集成设计。
- [x] 14.2 `docs/deploy-mac-lan.md` 包含 `INTERNAL_EML_<DOMAIN>_BASEURL` 与 `INTERNAL_EML_API_KEY` 环境变量。
- [x] 14.3 README 顶段提到"内网 EML 邮件服务器"。

## 15. 测试与验收

- [x] 15.1 端到端脚本：创建 internal_eml 账号 → GET → PUT（模拟编辑抽屉 save）→ 校验 account_type 不被降级 → 校验 imap_password 仍可解密 → /refresh 端点找到账号（不是 404）。
- [x] 15.2 单元覆盖 `_is_empty`：`b'EMPTY'`、`b'EMPTY\n'`、`b'EMPTYBODY...'`、`b''` 四种边界。
- [x] 15.3 单元覆盖 `_extract_filename`：classic / quoted / RFC 5987 / percent-encoded 四种形式。
- [x] 15.4 全量 pytest 单文件运行无回归（与本次相关测试 152 passed / 1 pre-existing）。
