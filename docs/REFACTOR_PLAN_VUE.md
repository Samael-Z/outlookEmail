# 项目 Vue 重构计划 (dev-vue)

> **目标**：把现有 Flask + Jinja + 原生 JS 的单体页面重构为「Flask 纯 API + Vue 3 SPA」前后端分离架构，UI 风格对齐 [Soybean Admin](https://soybeanjs.cn)，同时增加 `@cs2jp.com` / `@jokerque.com` 两个内网邮箱域名的接入能力。
>
> **分支**：`dev-vue`（基于 `dev` 创建）
> **完成定义**：dev-vue 分支可独立构建产物，功能与现有 v2.0.53 等价或更优，新内网 EML 邮箱接入完成端到端可用。

---

## 一、技术栈与版本（基于 Soybean Admin 2.2.0）

### 前端
| 维度 | 选型 | 来源 / 备注 |
|---|---|---|
| 框架 | **Vue 3.5** | composition API |
| 构建 | **Vite 8** | dev server + 生产构建 |
| 语言 | **TypeScript 6** | 严格模式 |
| UI 组件 | **Naive UI 2.44** | Soybean 默认；颜值高、TS 友好 |
| CSS 引擎 | **UnoCSS** (`@sa/uno-preset`) | atomic CSS，按需生成 |
| 状态管理 | **Pinia 3** | 替代 Vuex |
| 路由 | **vue-router 5** + **Elegant Router 0.3** | 文件式自动生成路由 |
| HTTP | **@sa/axios** (Soybean 封装) | 拦截器统一处理鉴权、错误 |
| 国际化 | **vue-i18n 11** | 至少中英两套，可后续扩展 |
| 图标 | **@iconify/vue** + **unplugin-icons** | 全套 iconify 集合 |
| 图表 | **ECharts 6** | 转发统计、刷新成功率 |
| 工具 | **@vueuse/core**、**dayjs**、**clipboard** | 日期、剪贴板等 |
| 包管理 | **pnpm** | 配合 Soybean monorepo 风格 |

### 后端（保持不变 + 少量改造）
| 维度 | 选型 |
|---|---|
| 框架 | **Flask 3.0+** 保持 |
| 数据库 | **SQLite 3** 保持，schema 兼容 |
| 调度 | APScheduler + croniter 保持 |
| 鉴权 | **沿用 Flask session（HttpOnly Cookie）**，CSRF 切到 Double-Submit Cookie 模式 |
| 进度推送 | **SSE 保持**（EventSource 在浏览器原生支持，跨 Vue SPA 没问题） |
| 新增 | `outlook_web/segments/10_routes_internal_eml.py`（内网 EML 适配） |

### 部署
| 模式 | 构建产物 |
|---|---|
| Docker | 多阶段 Dockerfile：node:20-alpine 构建前端 dist → python:3.11-slim 承载 Flask + 静态资源 |
| Windows EXE | PyInstaller spec 把 `web/dist/` 加入 `datas`，Flask 直接 serve |
| Python 直跑 | 开发模式下 Vite dev server (5173) + Flask (5000) 跨端口，Vite 配 proxy；生产模式同 Docker |

---

## 二、目录结构（重构后）

```
outlookEmail/
├── web/                          # 【新增】Vue SPA 源码
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── vite.config.ts
│   ├── uno.config.ts
│   ├── tsconfig.json
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── assets/
│   │   ├── components/           # 通用组件
│   │   ├── constants/            # 枚举、常量（账号类型、邮件状态等）
│   │   ├── hooks/                # composables
│   │   ├── layouts/              # 布局（默认 / 登录 / 全屏）
│   │   ├── locales/              # zh-CN.json / en-US.json
│   │   ├── plugins/              # naive-ui、i18n、pinia 注册
│   │   ├── router/               # Elegant Router 配置
│   │   ├── service/              # axios 封装 + API 模块
│   │   │   ├── request/
│   │   │   └── api/
│   │   │       ├── auth.ts
│   │   │       ├── groups.ts
│   │   │       ├── accounts.ts
│   │   │       ├── emails.ts
│   │   │       ├── temp-emails.ts
│   │   │       ├── internal-eml.ts   # 【新增】
│   │   │       ├── refresh.ts
│   │   │       ├── settings.ts
│   │   │       └── system.ts
│   │   ├── store/                # Pinia stores
│   │   ├── styles/               # 全局 scss
│   │   ├── theme/                # Soybean 主题配置
│   │   ├── typings/              # 全局类型
│   │   ├── utils/
│   │   └── views/                # 页面
│   │       ├── _builtin/login/
│   │       ├── home/             # 仪表盘
│   │       ├── mailbox/          # 主三栏邮件视图（账号 / 列表 / 详情）
│   │       ├── accounts/         # 账号管理
│   │       ├── temp-emails/      # 临时邮箱
│   │       ├── refresh/          # Token 刷新管理
│   │       ├── forwarding/       # 转发管理
│   │       ├── webdav/           # WebDAV 备份
│   │       └── settings/         # 系统设置
│   └── dist/                     # 构建产物（gitignored）
│
├── outlook_web/                  # Flask 后端（基本不动）
│   └── segments/
│       ├── 01_bootstrap.py
│       ├── 02_groups_accounts.py
│       ├── 03_mail_helpers.py
│       ├── 04_routes_groups_accounts.py
│       ├── 05_routes_refresh_mail.py
│       ├── 06_routes_temp_email.py
│       ├── 07_routes_oauth_settings_external.py
│       ├── 08_forwarding_scheduler_errors.py
│       ├── 09_routes_system_update.py
│       └── 10_routes_internal_eml.py    # 【新增】
│
├── templates/                    # 【弃用，保留作为回滚 fallback】
├── static/                       # 【弃用，保留作为回滚 fallback】
├── Dockerfile                    # 【改为多阶段】
├── outlookEmail.spec             # 【更新 datas 引入 web/dist】
└── .github/workflows/            # 【release.yml 增加前端构建步骤】
```

---

## 三、后端改造清单

### 3.1 路由现状盘点（共 100+ 路由，几乎全是 /api/*）

**仅 5 个非 API 路由需要处理**：

| 路由 | 现状 | 改造方案 |
|---|---|---|
| `GET /login` | 渲染 `templates/login.html` | 改为返回 Vue `dist/index.html`，登录页由前端路由 `/login` 处理 |
| `POST /login` | 接受 form/json，写 session | **保持不变** |
| `GET /logout` | 清 session → redirect | 改为 JSON 响应；重定向由前端处理 |
| `GET /` | 渲染 `templates/index.html` | 改为返回 Vue `dist/index.html`（SPA 入口） |
| `GET /favicon.ico` | 返回内联 SVG | 保持不变 |
| `GET /assets/index.css` | 拼接 8 个 CSS 片段 | **删除**（Vite 接管 CSS bundle） |

### 3.2 SPA 入口路由 + 静态资源服务

**新增一个 catch-all 路由把所有非 `/api/*` 请求都返回 `dist/index.html`**，由 Vue Router 处理：

```python
# outlook_web/segments/00_spa_serve.py（新增，最先加载）
from flask import send_from_directory
WEB_DIST = resource_path('web', 'dist')

@app.route('/assets/<path:filename>')
def spa_assets(filename):
    return send_from_directory(WEB_DIST / 'assets', filename)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def spa_index(path):
    # 排除已注册的 /api/* 和 /favicon.ico
    if path.startswith('api/') or path == 'favicon.ico':
        abort(404)
    return send_from_directory(WEB_DIST, 'index.html')
```

### 3.3 鉴权改造

**继续用 Flask session（cookie）+ Double-Submit CSRF Token**：

- 登录成功后 `Set-Cookie: session=...; HttpOnly; SameSite=Lax`
- 前端首次启动调 `GET /api/csrf-token` 拿到 token，axios 拦截器把 token 写到 `X-CSRF-Token` header
- 后端 `flask-wtf` 校验 header 中的 token
- 所有 `/api/*` 受 `@login_required` 保护，未登录返回 401，前端拦截 401 跳 `/login`

**SSE 鉴权**：EventSource 自动带 cookie，复用 session 即可，无需特殊处理。

### 3.4 CORS

生产模式下前后端**同源部署**（都通过 Flask），不需要 CORS。
开发模式下 Vite (5173) → Flask (5000)，由 **Vite proxy** 解决（不用 CORS）：

```ts
// web/vite.config.ts
server: {
  proxy: {
    '/api': 'http://127.0.0.1:5000',
    '/login': 'http://127.0.0.1:5000',
    '/logout': 'http://127.0.0.1:5000',
  }
}
```

---

## 四、内网 EML 邮箱接入（@cs2jp.com / @jokerque.com）

### 4.1 数据模型（沿用 accounts 表，零迁移）

复用现有字段，新增一个 `account_type` 值：

| 字段 | 内网 EML 账号取值 |
|---|---|
| `account_type` | `'internal_eml'` |
| `provider` | `'internal_eml'` |
| `email` | 用户邮箱地址（如 `xxx@jokerque.com`） |
| `imap_host` | baseURL（如 `http://mail.jokerque.com:8080`）—— **借字段，命名不改** |
| `imap_password` | api_key（如 `eml_server_private_KEY_2023`） |
| `password` | 留空或 NULL |
| `client_id` / `refresh_token` | NULL |

> 域名 → baseURL 路由表内置（环境变量可覆盖），导入时根据邮箱后缀自动填 baseURL：
>
> ```python
> INTERNAL_EML_DOMAIN_BASEURL = {
>     'cs2jp.com': os.getenv('INTERNAL_EML_CS2JP_BASEURL', 'http://cs-email-manager.17usoft.com'),
>     'jokerque.com': os.getenv('INTERNAL_EML_JOKERQUE_BASEURL', 'http://mail.jokerque.com:8080'),
> }
> INTERNAL_EML_DEFAULT_KEY = os.getenv('INTERNAL_EML_API_KEY', 'eml_server_private_KEY_2023')
> ```

### 4.2 新增 segment：`10_routes_internal_eml.py`

**核心 helper**（Python 翻译 Go SDK）：

```python
import hashlib, time, requests
from urllib.parse import urlencode

class InternalEmlClient:
    def __init__(self, base_url: str, private_key: str, proxies: dict | None = None):
        self.base_url = base_url.rstrip('/')
        self.private_key = private_key
        self.proxies = proxies

    def _sign(self, suffix: str) -> tuple[str, str]:
        ts = str(int(time.time()))
        sig = hashlib.md5((ts + self.private_key + suffix).encode()).hexdigest()
        return ts, sig

    def get_email(self, email: str) -> tuple[bytes, str] | None:
        ts, sig = self._sign(email)
        qs = urlencode({'timestamp': ts, 'signature': sig, 'email': email})
        r = requests.get(f'{self.base_url}/get?{qs}', proxies=self.proxies, timeout=30, verify=False)
        if r.status_code != 200:
            return None
        if r.content == b'EMPTY':
            return None
        filename = self._extract_filename(r.headers.get('Content-Disposition', ''))
        return r.content, filename

    def download_next(self) -> tuple[bytes, str] | None:
        ts, sig = self._sign('')
        qs = urlencode({'timestamp': ts, 'signature': sig})
        r = requests.get(f'{self.base_url}/download?{qs}', proxies=self.proxies, timeout=30, verify=False)
        if r.status_code != 200 or r.content == b'EMPTY':
            return None
        return r.content, self._extract_filename(r.headers.get('Content-Disposition', ''))

    def delete(self, filename: str) -> bool:
        ts, sig = self._sign(filename)
        qs = urlencode({'timestamp': ts, 'signature': sig, 'filename': filename})
        r = requests.get(f'{self.base_url}/delete?{qs}', proxies=self.proxies, timeout=30, verify=False)
        return r.status_code == 200

    @staticmethod
    def _extract_filename(content_disposition: str) -> str:
        ...  # 解析 filename="xxx" 或 filename=xxx
```

**EML 解析**：Python 标准库

```python
from email import policy
from email.parser import BytesParser

def parse_eml(content: bytes) -> dict:
    msg = BytesParser(policy=policy.default).parsebytes(content)
    return {
        'subject': str(msg['Subject']),
        'from': str(msg['From']),
        'to': str(msg['To']),
        'date': str(msg['Date']),
        'text': msg.get_body(preferencelist=('plain',)).get_content() if msg.get_body(preferencelist=('plain',)) else '',
        'html': msg.get_body(preferencelist=('html',)).get_content() if msg.get_body(preferencelist=('html',)) else '',
        'attachments': [
            {'filename': p.get_filename(), 'content_type': p.get_content_type(), 'size': len(p.get_payload(decode=True) or b'')}
            for p in msg.iter_attachments()
        ],
    }
```

### 4.3 Consume-and-Delete 模式的处理

**关键问题**：内网 SDK 的 `/get` 是消费式的，不删则下次还会拿到同一封，跟现有 IMAP / Graph "读后保留" 语义冲突。

**方案**：本地落库 + 自动删除

新增表 `internal_eml_messages`：

```sql
CREATE TABLE IF NOT EXISTS internal_eml_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    email TEXT NOT NULL,
    server_filename TEXT NOT NULL,         -- 服务端返回的 .eml 文件名
    subject TEXT,
    from_addr TEXT,
    to_addr TEXT,
    body_text TEXT,
    body_html TEXT,
    has_attachment INTEGER DEFAULT 0,
    raw_eml BLOB,                          -- 原始 EML（用于下载附件）
    received_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read INTEGER DEFAULT 0,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);
CREATE INDEX idx_iem_account_received ON internal_eml_messages(account_id, received_at DESC);
```

刷新流程：

```
for each internal_eml 账号:
    while True:
        result = client.get_email(account.email)
        if result is None: break
        content, filename = result
        parsed = parse_eml(content)
        INSERT INTO internal_eml_messages (...)
        client.delete(filename)
```

### 4.4 API 端点（新增）

```
GET    /api/internal-eml/<account_id>/messages          列表（带分页、关键词搜索）
GET    /api/internal-eml/<account_id>/messages/<msg_id> 详情
DELETE /api/internal-eml/<account_id>/messages/<msg_id> 删除（仅本地，服务端已删）
POST   /api/internal-eml/<account_id>/refresh           手动拉取
GET    /api/internal-eml/<account_id>/messages/<msg_id>/attachments/<idx>  附件下载
```

### 4.5 与现有刷新链路集成

- `account_type='internal_eml'` 的账号在批量刷新逻辑里走 `InternalEmlClient` 分支
- 在 `08_forwarding_scheduler_errors.py` 的定时刷新中纳入
- 不参与 OAuth Token 刷新（没有 token），但 UI 上"全量刷新"要把这类账号也跑一遍 `/refresh`

### 4.6 账号导入格式

**界面新增一个导入分类「内网 EML 邮箱」**，格式：

```txt
# 自动按域名路由 baseURL（推荐）
xxx@jokerque.com----eml_server_private_KEY_2023
xxx@cs2jp.com----eml_server_private_KEY_2023

# 自定义 baseURL（兜底）
xxx@example.com----api-key----http://custom-server:8080
```

---

## 五、UI 重构清单（按页面）

> 三栏邮件视图沿用 Soybean Admin 的「双侧栏 + 主内容」布局，但内部用 Naive UI 的 `n-split` / `n-layout` 实现"分组 / 账号 / 邮件列表 / 邮件详情"四栏。

| Vue 页面 | 对应原页面 | Naive UI 关键组件 |
|---|---|---|
| `_builtin/login` | `login.html` | `n-card`, `n-input`, `n-button`, `n-form` |
| `home` | （新增）仪表盘 | `n-grid` + `n-statistic` + ECharts |
| `mailbox/index` | `index.html`（核心四栏） | `n-split`, `n-list`, `n-virtual-list`, `n-empty` |
| `accounts/list` | 邮箱管理弹窗 | `n-data-table`, `n-checkbox`, `n-dropdown` |
| `accounts/import` | 导入邮箱弹窗 | `n-modal`, `n-input` (textarea), `n-radio-group` |
| `accounts/edit` | 编辑账号 | `n-drawer`, `n-form`, `n-dynamic-input` (别名) |
| `temp-emails/index` | 临时邮箱 | `n-tabs` (GPTMail / DuckMail / Cloudflare), `n-list` |
| `refresh/index` | Token 刷新管理 | `n-progress`, `n-timeline`, SSE 实时进度 |
| `forwarding/index` | 转发设置 + 历史 | `n-form`, `n-data-table`, `n-tag` |
| `webdav/index` | WebDAV 备份 | `n-form`, `n-input`, `n-button` |
| `settings/index` | 系统设置 | `n-tabs` + 多组 `n-form` |
| `mailbox/internal-eml` | 【新增】内网 EML 邮箱视图 | 复用 mailbox 主视图 + 类型标识 |

### 5.1 Soybean 视觉特征复用

- **Sider 折叠 + 主题切换**：默认浅色 + 深色 + 跟随系统
- **主色**：保留 Soybean 默认 `#646cff` 或改为现有 `#667eea`（参考 appleemail.top 的紫蓝渐变）
- **Tab Bar**：多标签页（用户在账号、邮件、设置间切换不丢上下文）
- **面包屑**：自动根据路由生成
- **顶部全局搜索**：复用现有"全局搜索"功能
- **图标系统**：全量切到 `@iconify/json` + tabler / material-symbols 集合

---

## 六、打包与部署改造

### 6.1 新 Dockerfile（多阶段）

```dockerfile
# Stage 1: 构建前端
FROM node:20-alpine AS web-builder
WORKDIR /web
COPY web/package.json web/pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY web/ ./
RUN pnpm build

# Stage 2: Python 运行时
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install gunicorn

COPY . .
COPY --from=web-builder /web/dist /app/web/dist

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 GUNICORN_TIMEOUT=300 GUNICORN_THREADS=4

EXPOSE 5000
CMD ["sh", "-c", "gunicorn -k gthread -w 1 --threads ${GUNICORN_THREADS:-4} -b 0.0.0.0:5000 --timeout ${GUNICORN_TIMEOUT:-300} --graceful-timeout 30 --access-logfile - --error-logfile - --capture-output web_outlook_app:app"]
```

### 6.2 PyInstaller spec 更新

```python
# outlookEmail.spec
datas = [
    (str(project_root / "templates"), "templates"),    # 保留作为 fallback
    (str(project_root / "static"), "static"),          # 保留作为 fallback
    (str(project_root / "outlook_web" / "segments"), "outlook_web/segments"),
    (str(project_root / "VERSION"), "."),
    (str(project_root / "web" / "dist"), "web/dist"),  # 【新增】Vue 构建产物
]
```

**构建顺序**：Windows runner 上先 `pnpm install && pnpm build`，再 `pyinstaller`。

### 6.3 release.yml 工作流改造

```yaml
build-windows-exe:
  steps:
    - uses: actions/checkout@v6
    - uses: actions/setup-node@v4
      with:
        node-version: '20'
    - uses: pnpm/action-setup@v3
      with:
        version: 9
    - name: Build frontend
      working-directory: web
      run: pnpm install --frozen-lockfile && pnpm build
    - uses: actions/setup-python@v6
      with:
        python-version: '3.12'
    - run: pip install -r requirements.txt pyinstaller
    - run: pyinstaller --noconfirm --clean outlookEmail.spec
    - ... # 打包上传
```

### 6.4 开发模式

```bash
# 后端
python web_outlook_app.py     # :5000

# 前端
cd web
pnpm install
pnpm dev                       # :5173, 通过 vite proxy 代理 /api 到 :5000
```

---

## 七、关键风险与决策点

| 风险 | 影响 | 缓解方案 |
|---|---|---|
| **PyInstaller 打包后 Vue 资源路径问题** | exe 启动后 SPA 资源 404 | 用 `resource_path('web', 'dist')` + `sys._MEIPASS` 解析；本地 test 验证 |
| **Vite base path** | 生产部署在非根路径会破 router | 默认 `base: '/'`，文档明示 |
| **SSE 在 nginx / Cloudflare 后** | 连接易被中断 | 后端发心跳 + 前端 EventSource onerror 自动重连（已有逻辑） |
| **CSRF 在 SPA 下的体验** | 首屏要先调 `/api/csrf-token` | axios 启动时同步调一次；token 写到 localStorage + cookie |
| **内网 EML consume-and-delete 不可逆** | 服务端删了找不回 | 本地必须先成功落库再发 delete；落库失败不删 |
| **新数据库表 `internal_eml_messages` 迁移** | 老库升级 | 用现有的 `CREATE TABLE IF NOT EXISTS` 风格，无破坏性 |
| **现有 templates/static 弃用顺序** | 误删致回滚困难 | 阶段 1-4 保留双轨；阶段 5 完成验收后再删 |
| **首屏体积** | Vue + Naive UI gzip 后 ~300KB | 已可接受；后续按需 import 优化 |

---

## 八、分阶段执行路线图

> 每阶段产出物：可独立验证 + 可独立提交 PR。

### 阶段 0：基线（已完成 ✅）
- [x] 新建 `dev-vue` 分支
- [x] 调研 Soybean Admin 仓库结构与依赖
- [x] 盘点后端 100+ 路由，确认几乎全是 API
- [x] 设计鉴权方案（沿用 session + CSRF）
- [x] 设计内网 EML 接入数据模型

### 阶段 1：前端脚手架（1-2 天）
- [ ] `web/` 目录初始化（直接 fork Soybean Admin 主仓最小子集，删除示例 views/store）
- [ ] 配 `vite.config.ts` 的 proxy 指向 :5000
- [ ] 接通登录页 + 首页空壳，验证开发模式可登录、可调 API
- [ ] CI: 加 `pnpm install && pnpm build` 步骤到 release.yml

### 阶段 2：API 客户端 + 状态管理（1-2 天）
- [ ] `src/service/request/` axios 封装（拦截器、CSRF、错误统一处理）
- [ ] `src/service/api/` 按现有后端 9 个 segment 拆 API 模块
- [ ] Pinia stores：`useAuthStore`, `useGroupStore`, `useAccountStore`, `useEmailStore`, `useTempEmailStore`, `useSettingsStore`

### 阶段 3：核心页面重构（5-7 天，可并行）
- [ ] 登录页
- [ ] 主邮件视图（四栏：分组 / 账号 / 邮件列表 / 详情）
- [ ] 账号管理（列表 + 导入 + 编辑 + 批量操作）
- [ ] 临时邮箱
- [ ] 设置中心
- [ ] Token 刷新管理（含 SSE）
- [ ] 转发 / WebDAV

### 阶段 4：内网 EML 邮箱接入（2-3 天）
- [ ] `outlook_web/segments/10_routes_internal_eml.py` 实现 `InternalEmlClient` + 6 个端点
- [ ] schema 新增 `internal_eml_messages` 表
- [ ] 现有刷新调度链路接入
- [ ] 账号导入弹窗增加「内网 EML」分类 + 域名自动路由
- [ ] 主邮件视图支持显示这类账号（与普通账号同一三栏视图）

### 阶段 5：打包与部署（1-2 天）
- [ ] Dockerfile 改多阶段，本地验证 `docker build` + `docker run`
- [ ] PyInstaller spec 加 `web/dist` 到 datas，本地构建 exe 验证
- [ ] release.yml 增加前端构建步骤
- [ ] 更新 README / RELEASE.md

### 阶段 6：弃用旧前端 + 回归测试（1-2 天）
- [ ] 删除 `templates/index.html`、`templates/login.html`
- [ ] 删除 `static/js/index/`、`static/css/index/`
- [ ] 完整功能回归：登录、分组、账号增删改、收信、转发、刷新、临时邮箱、内网 EML、设置
- [ ] 性能对比（首屏、切账号速度）
- [ ] 合并 `dev-vue` → `dev` → `main`

**总工时估算**：13-19 个工作日。

---

## 九、待用户确认的决策点

在阶段 1 启动前需要拍板：

1. **是直接基于 Soybean Admin 主仓裁剪，还是用 `soybeanjs/soybean-admin-template-lite` 这种精简模板？**
   - 推荐主仓裁剪（功能更全），代价是初次清理 1-2 小时
2. **主色保留 Soybean 默认 `#646cff`，还是对齐之前看的 appleemail.top 的紫蓝渐变 `#667eea → #764ba2`？**
3. **i18n 是否启用？**（默认只做中文，预留 en-US 文件结构）
4. **内网 EML 邮箱的 baseURL 是固定写死还是允许账号级覆盖？**
   - 当前设计：域名 → baseURL 表内置 + 环境变量可覆盖 + 账号导入允许自定义（兜底）
5. **多标签页（tab bar）是否启用？**
   - Soybean 默认开，使用感比较好；但首屏体积略大

---

## 十、关联资料

- Soybean Admin GitHub: https://github.com/soybeanjs/soybean-admin
- Soybean Admin 官网: https://soybeanjs.cn
- Naive UI: https://www.naiveui.com
- UnoCSS: https://unocss.dev
- Elegant Router: https://github.com/soybeanjs/elegant-router
- 内网 EML SDK 源码: `E:\dextern\workspace\vibecoding\kiroRE\eml\sdk\client.go`
- 内网 EML 协议详情: 见 memory `reference_internal_eml_sdk.md`
