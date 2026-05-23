## 背景与动机

项目已经支持 Outlook OAuth + Microsoft Graph、标准 IMAP（Gmail / QQ / 163 / 126 / Yahoo / 阿里 / 自定义）和三类临时邮箱（GPTMail / DuckMail / Cloudflare Temp Email）。但内网搭建的 EML 邮件服务器（域名 `@cs2jp.com` 与 `@jokerque.com`）没有 IMAP、没有 Graph，只暴露一组带 MD5 签名的 HTTP GET 端点：

- `GET /download?timestamp=&signature=` — 拉队列下一封 EML
- `GET /get?timestamp=&signature=&email=<addr>` — 按收件人拉指定邮件
- `GET /delete?timestamp=&signature=&filename=<name>` — 按文件名删除

需要接入这套服务器作为第四种邮件读取链路，并把它当作"自助搭建的临时邮箱"使用：随机生成邮箱名 → 接收验证码 → 拉取后立即从服务端删除（释放硬盘）。

## 变更内容

- 新增 `outlook_web/segments/10_routes_internal_eml.py`：协议客户端 `InternalEmlClient`、EML 解析、域名 → baseURL 路由表、消费式拉取 + 落库 + 服务端自动删除、6 个 HTTP 端点 + 1 个随机生成端点。
- 复用 `accounts` 表承载新类型：`account_type='internal_eml'`、`provider='internal_eml'`、`imap_host` 借字段存 baseURL、`imap_password` 借字段存 api_key（与其他类型一样经 `encrypt_data` 加密）。
- 新增持久化表 `internal_eml_messages` 用于本地落库已消费邮件（含 raw EML，便于附件下载）。
- 修改 `04_routes_groups_accounts.py` 的 `api_update_account` 与 `08_forwarding_scheduler_errors.py` 中的 `api_update_account_v2`：加入 `is_internal_eml` 分支，保留 `account_type/provider`，避免被降级成 `imap/custom`。
- 修改 `08_forwarding_scheduler_errors.py` 的转发调度 SQL，排除 `account_type='internal_eml'`，避免对空 Graph 凭据刷屏失败日志。
- 前端 Vue：`/internal-eml` 专用页面（三栏：账号、邮件列表、详情）+ 顶级 🎲 随机生成按钮 + 复制邮箱按钮 + 账号管理页内的"内网 EML"导入分类。
- 邮箱视图（`/mailbox`）显式过滤 `internal_eml` 账号，使其只出现在专用页面，不污染按 provider 分类的左栏。

## 能力范围

### 新增能力

- `internal-eml-mail`：通过签名 HTTP 协议拉取内网 EML 服务器邮件，落本地库后立即删除服务端，并提供本地浏览 / 详情 / 附件 / 删除能力。

### 修改能力

- `account-update`（隐式）：`PUT /api/accounts/<id>` 增加 internal_eml 类型分支。
- `forwarding-scheduler`（隐式）：调度 SQL 排除 internal_eml 账号。

## 影响范围

- 新增段：`outlook_web/segments/10_routes_internal_eml.py`。
- 修改段：`outlook_web/segments/04_routes_groups_accounts.py`、`outlook_web/segments/08_forwarding_scheduler_errors.py`。
- 新增表：`internal_eml_messages`（带 `(account_id, server_filename)` 唯一索引，避免重复入库）。
- 段加载：`web_outlook_app.py` 的 `SEGMENT_FILES` 在 9 与 11 之间加入 10。
- 前端：`web/src/views/internal-eml/`、`web/src/views/mailbox/`、`web/src/components/InternalEmlImportDialog.vue`、`web/src/service/api/internal-eml.ts`。
- 部署文档：`docs/deploy-mac-lan.md` 包含 `INTERNAL_EML_<DOMAIN>_BASEURL` 与 `INTERNAL_EML_API_KEY` 环境变量。

## 非目标

- 不修改任何现有 IMAP / Graph / 临时邮箱链路。
- 不支持 HTTPS 校验 verify=True（内网协议默认 HTTP）— 后续若启用 HTTPS 再扩。
- 不为内网邮件接入转发或 WebDAV 备份链路。
- 不暴露到对外 API Key 接口（`/api/external/*`）— 仅 session 登录可见。
