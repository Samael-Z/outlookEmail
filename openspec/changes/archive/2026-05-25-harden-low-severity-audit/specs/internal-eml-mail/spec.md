## MODIFIED Requirements

### Requirement: Internal EML protocol client
系统 SHALL 通过签名 HTTP GET 协议访问内网 EML 邮件服务器，行为与项目主人提供的 Go SDK 一致；并 SHALL 在 HTTPS baseURL 下默认启用 TLS 证书校验。

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

#### Scenario: HTTPS 默认校验证书
- **WHEN** 内网 EML 账号的 baseURL 以 `https://` 开头，且未显式禁用 TLS 校验
- **THEN** 客户端 SHALL 以 `verify=True` 发起 requests 调用。

#### Scenario: HTTP 跳过校验是 noop
- **WHEN** baseURL 以 `http://` 开头
- **THEN** 客户端 SHALL 以 `verify=False` 发起调用，且 SHALL NOT 触发 urllib3 的 InsecureRequestWarning。

#### Scenario: 环境变量显式禁用 TLS 校验
- **WHEN** 环境变量 `INTERNAL_EML_INSECURE` 为 truthy 值（`1`/`true`/`yes`/`on`）
- **THEN** `_build_client_for_account` SHALL 把 `verify_tls=False` 传给客户端，即使 baseURL 是 `https://`。
