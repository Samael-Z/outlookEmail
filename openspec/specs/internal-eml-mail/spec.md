# internal-eml-mail Specification

## Purpose

本规范定义内网搭建的 EML 邮件服务器接入契约。覆盖签名 HTTP 协议、`accounts` 表借字段、域名 → baseURL 路由、consume-and-delete 拉取循环、随机邮箱生成、本地浏览能力，以及与现有账号更新 / 转发调度 / 邮箱视图三处交互点的隔离规则。

参考实现：`outlook_web/segments/10_routes_internal_eml.py`。

## Requirements

### Requirement: Internal EML protocol client
系统 SHALL 通过签名 HTTP GET 协议访问内网 EML 邮件服务器，行为与项目主人提供的 Go SDK 一致。

#### Scenario: 签名生成
- **WHEN** 系统需要向内网 EML 服务器发送任意一类请求
- **THEN** 系统 SHALL 计算 `timestamp = str(int(time.time()))`、`signature = md5(timestamp + private_key + suffix).hex()`；其中 suffix 为 `/download` 时为空字符串、`/get` 时为收件人邮箱、`/delete` 时为目标文件名。

#### Scenario: 队列空响应识别
- **WHEN** 系统收到服务端响应，其响应体经 `strip()` 后等于字面量 `b"EMPTY"`
- **THEN** 系统 SHALL 视为"队列为空"并停止当前 drain 循环。

#### Scenario: 非空响应识别
- **WHEN** 系统收到服务端响应，其响应体经 `strip()` 后不等于 `b"EMPTY"`（即使响应体的字节序列以 'EMPTY' 字节开头）
- **THEN** 系统 SHALL 视为有效 EML 内容并继续解析。

#### Scenario: 文件名提取
- **WHEN** 系统从响应头解析 `Content-Disposition`
- **THEN** 系统 SHALL 优先使用 RFC 5987 的 `filename*=<charset>'<lang>'<percent-encoded>` 形式并按声明 charset 解码；缺失时回退到 `filename="..."`；再缺失时回退到 `filename=...`；都不存在时返回空字符串。

#### Scenario: 代理与超时
- **WHEN** 账号关联的分组配置了 `proxy_url`
- **THEN** 系统 SHALL 通过 `requests.get(..., proxies={'http': proxy_url, 'https': proxy_url}, timeout=30)` 发起调用。

### Requirement: Internal EML account storage
系统 SHALL 复用现有 `accounts` 表承载内网 EML 账号，并将敏感凭据加密存储。

#### Scenario: 账号类型标识
- **WHEN** 系统创建内网 EML 账号
- **THEN** `account_type` SHALL 等于 `'internal_eml'`，`provider` SHALL 等于 `'internal_eml'`，`imap_port` SHALL 等于 0。

#### Scenario: baseURL 借字段
- **WHEN** 系统创建或更新内网 EML 账号
- **THEN** `imap_host` 字段 SHALL 存储该账号的内网 EML 服务器 baseURL；为空时由域名 → baseURL 路由表兜底解析。

#### Scenario: api_key 加密存储
- **WHEN** 系统创建或更新内网 EML 账号
- **THEN** `imap_password` 字段 SHALL 存储经 `encrypt_data` 加密的 api_key；读取时 SHALL 经 `decrypt_data` 还原。

#### Scenario: 创建时缺省值
- **WHEN** 创建端点未显式提供 `api_key`
- **THEN** 系统 SHALL 使用 `get_internal_eml_default_key()` 返回值（环境变量 `INTERNAL_EML_API_KEY` 优先于内置默认）。

#### Scenario: 创建时缺省 baseURL
- **WHEN** 创建端点未显式提供 `base_url`，但 `email` 域名命中域名 → baseURL 路由表
- **THEN** 系统 SHALL 使用路由表查找结果作为 `imap_host` 写入数据库。

#### Scenario: 创建时域名无法解析
- **WHEN** 创建端点既未提供 `base_url`，且 `email` 域名不在路由表内
- **THEN** 系统 SHALL 返回 400，并说明域名无法解析。

### Requirement: Domain to baseURL routing
系统 SHALL 通过内置常量与环境变量提供域名 → baseURL 的路由能力。

#### Scenario: 内置域名表
- **WHEN** 系统首次加载 segment
- **THEN** 系统 SHALL 暴露内置域名表 `INTERNAL_EML_DOMAIN_BASEURL_DEFAULT`，至少包含 `cs2jp.com` 与 `jokerque.com` 两个键。

#### Scenario: 环境变量覆盖
- **WHEN** 环境变量 `INTERNAL_EML_<DOMAIN_UPPER>_BASEURL` 已设置（域名中的点用下划线替代）
- **THEN** `get_internal_eml_baseurl_for_domain(domain)` SHALL 返回环境变量值，并忽略内置默认。

#### Scenario: 配置查询端点
- **WHEN** 已登录用户请求 `GET /api/internal-eml/config/domains`
- **THEN** 系统 SHALL 返回当前可用域名 → baseURL 映射，以及当前 default api_key 是否存在。

### Requirement: Consume-and-delete fetch loop
系统 SHALL 在拉取邮件后立即从服务端删除，避免内网服务器累积已读 EML 文件。

#### Scenario: 落库后才删
- **WHEN** 系统从服务端获取一封邮件
- **THEN** 系统 SHALL 先解析并 `INSERT INTO internal_eml_messages` 并 `commit()`，commit 成功后才调用 `client.delete(filename)`。

#### Scenario: 落库失败不删
- **WHEN** EML 解析或 INSERT 失败
- **THEN** 系统 SHALL NOT 调用 `client.delete`，避免数据永久丢失。

#### Scenario: 单次 delete 失败继续
- **WHEN** 服务端对某次 `/delete` 返回错误
- **THEN** 系统 SHALL 记录错误到 `error` 字符串、`continue` 处理下一封，且 SHALL NOT 中断整轮 drain。

#### Scenario: 重复 fetch 幂等
- **WHEN** 由于上一轮 delete 失败导致同一服务端文件再次被 `/get` 拉到
- **THEN** `INSERT OR IGNORE` 配合 `(account_id, server_filename)` 唯一索引 SHALL 跳过重复，本地不会产生重复行。

#### Scenario: drain 上限保护
- **WHEN** 一次 `/refresh` 持续 drain
- **THEN** 系统 SHALL 在最多 200 封后终止本轮 drain，避免阻塞 worker 线程。

### Requirement: Random mailbox generation
系统 SHALL 提供一个端点，原子化生成随机内网 EML 邮箱并创建账号。

#### Scenario: 生成端点
- **WHEN** 已登录用户请求 `POST /api/internal-eml/accounts/generate-random`，可选传入 `{ domain, prefix_length, group_id, remark }`
- **THEN** 系统 SHALL 使用 `secrets.choice` 从 `[a-z0-9]` 池生成随机前缀，与指定域名拼接成完整邮箱地址；INSERT 时 `imap_password` 用 `encrypt_data(default_api_key)` 加密；返回 `{success, account: {id, email, domain, base_url, group_id, remark}}`。

#### Scenario: 缺省前缀长度
- **WHEN** 请求未提供 `prefix_length`
- **THEN** 系统 SHALL 使用 10 作为默认值。

#### Scenario: 缺省域名
- **WHEN** 请求未提供 `domain`
- **THEN** 系统 SHALL 从可用域名表中随机挑选一个。

#### Scenario: 不支持的域名
- **WHEN** 请求指定的 `domain` 既不在内置表中、也无环境变量配置
- **THEN** 系统 SHALL 返回 400，并说明域名不支持。

#### Scenario: 冲突重试
- **WHEN** 生成的邮箱地址在 `accounts` 表已存在
- **THEN** 系统 SHALL 最多重试 5 次重新生成；都失败时返回 500 并说明冲突。

### Requirement: Internal EML message browsing
系统 SHALL 暴露分页、搜索、详情、附件下载、本地删除等本地浏览能力。

#### Scenario: 列表与分页
- **WHEN** 已登录用户请求 `GET /api/internal-eml/<account_id>/messages?page=&per_page=`
- **THEN** 系统 SHALL 限制 `per_page ≤ 100`，按 `COALESCE(received_at, fetched_at) DESC` 排序，返回 `{messages, total, page, per_page}`。

#### Scenario: 关键词搜索
- **WHEN** 请求附带 `keyword`
- **THEN** 系统 SHALL 在 subject / from_addr / body_text 三列做 LIKE `%keyword%` 模糊匹配。

#### Scenario: 详情读取与已读标记
- **WHEN** 已登录用户请求 `GET /api/internal-eml/<account_id>/messages/<msg_id>`
- **THEN** 系统 SHALL 返回完整 message + 附件元数据（filename / content_type / size），并将 `is_read` 置为 1。

#### Scenario: 附件下载
- **WHEN** 已登录用户请求 `GET /api/internal-eml/<account_id>/messages/<msg_id>/attachments/<att_idx>`
- **THEN** 系统 SHALL 从 `raw_eml` BLOB 解码并返回 `att_idx` 索引位置的附件二进制，附带 `Content-Disposition: attachment; filename=...` 头。

#### Scenario: 本地删除
- **WHEN** 已登录用户请求 `DELETE /api/internal-eml/<account_id>/messages/<msg_id>`
- **THEN** 系统 SHALL 删除本地行（服务端文件已在 fetch 时删除，不再二次调用 `/delete`）。

### Requirement: Account update preserves internal_eml type
系统 SHALL 在 `PUT /api/accounts/<id>` 路径上保留 internal_eml 类型，不再被降级为 imap+custom。

#### Scenario: 编辑保留类型
- **WHEN** 已登录用户对 `account_type='internal_eml'` 的账号发起 PUT 请求，请求体包含 `account_type: 'internal_eml'` 或 `provider: 'internal_eml'`
- **THEN** 系统 SHALL 进入 internal_eml 分支，保留 `account_type='internal_eml'` 与 `provider='internal_eml'`，清空 `client_id`/`refresh_token`/`password`、置 `imap_port=0`，且 SHALL NOT 改成 `account_type='imap'` 或 `provider='custom'`。

#### Scenario: 旧端点与覆盖端点都要修复
- **WHEN** 系统由 `04_routes_groups_accounts.py::api_update_account` 与 `08_forwarding_scheduler_errors.py::api_update_account_v2` 中任意一个承载 PUT 路由
- **THEN** 两份实现 SHALL 都包含 `is_internal_eml` 分支，且行为一致。

### Requirement: Forwarding scheduler excludes internal_eml
系统 SHALL 在转发调度阶段排除 internal_eml 账号，避免空 Graph 凭据导致刷屏失败。

#### Scenario: 调度查询过滤
- **WHEN** 转发调度器执行 `SELECT * FROM accounts WHERE status='active' AND forward_enabled=1`
- **THEN** 查询条件 SHALL 追加 `AND account_type != 'internal_eml'`。

#### Scenario: 即使用户开启转发也跳过
- **WHEN** 用户在内网 EML 账号上把 `forward_enabled` 置为 1
- **THEN** 该账号 SHALL NOT 出现在调度结果集中，转发日志 SHALL NOT 产生 internal_eml 相关失败记录。

### Requirement: Mailbox view excludes internal_eml
系统 SHALL 在按服务商分类的邮箱视图中过滤掉 internal_eml 类型，让它仅出现在 `/internal-eml` 专用页面。

#### Scenario: 邮箱视图账号过滤
- **WHEN** Vue `/mailbox` 页面调用 `accountsApi.listAccounts(...)` 后渲染左栏与账号列表
- **THEN** 系统 SHALL 过滤掉 `account_type === 'internal_eml'` 的账号，且 SHALL NOT 在按服务商分类的左栏中显示 "内网 EML" 项。

#### Scenario: 专用页面入口
- **WHEN** 用户需要查看内网 EML 邮件
- **THEN** 用户 SHALL 通过 `/internal-eml` 页面访问；该页面 SHALL 显示账号列表、邮件列表、邮件详情、附件下载、🎲 随机生成按钮、添加按钮、复制邮箱按钮、删除按钮。
