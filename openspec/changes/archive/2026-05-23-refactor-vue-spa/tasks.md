## 1. 后端 SPA 服务层

- [x] 1.1 新增 `outlook_web/segments/00_spa_serve.py`，集中暴露 `WEB_DIST_DIR`、`has_spa_build()`、`_serve_spa_or_fallback()`。
- [x] 1.2 新增 `outlook_web/segments/11_routes_spa_catchall.py`，注册 `/assets/<path:filename>` 与 `/<path:path>` 两条路由；显式拒绝 `api/` 与 `static/` 前缀；做路径越级校验。
- [x] 1.3 `web_outlook_app.py` 的 `SEGMENT_FILES` 在 `01_bootstrap.py` 之后加入 `00_spa_serve.py`，并在最末加入 `11_routes_spa_catchall.py`。

## 2. 现有路由调整

- [x] 2.1 `04_routes_groups_accounts.py`：`GET /login` 与 `GET /` 改为 `_serve_spa_or_fallback`；`/logout` 在 JSON / `/api/*` / POST 路径返回 JSON，其余路径走 SPA。
- [x] 2.2 删除 `bundled_index_css` 路由（被 Vite `/assets/index-<hash>.css` 取代）。
- [x] 2.3 `08_forwarding_scheduler_errors.py` 全局 `errorhandler(Exception)` 增加 `isinstance(error, HTTPException)` 分支保留原始状态码与描述。

## 3. 前端工程脚手架

- [x] 3.1 创建 `web/` 目录与 `package.json`（Vue 3.5 / Vite 8 / TypeScript 6 / Naive UI 2.44 / UnoCSS / Pinia 3 / vue-router / vue-i18n 11）。
- [x] 3.2 `vite.config.ts` 配置：`@` 别名、UnoCSS 插件、Auto-import + Components（NaiveUiResolver + IconsResolver）、dev server proxy `/api` → `:5000`。
- [x] 3.3 `tsconfig.json`、`uno.config.ts`（含主题色与 shortcut）、`env.d.ts`、`.gitignore`。
- [x] 3.4 `src/main.ts` 启动序列：Pinia → i18n → router → mount。
- [x] 3.5 `src/App.vue` 包裹 NConfigProvider + 5 个 NaiveUI Provider，绑定主题色与 locale。

## 4. 状态、服务、路由层

- [x] 4.1 Pinia stores：`auth`、`app`（locale + sider 折叠）、`theme`（dark + primary color）、`tab`（多标签）。
- [x] 4.2 `src/service/request/index.ts`：axios 实例 + CSRF token 拉取与缓存 + 401 重定向 + CSRF 失效透明重试一次。
- [x] 4.3 各业务 API service：`auth`、`accounts`、`emails`、`internal-eml`、`temp-emails`、`refresh`、`forwarding`、`webdav`、`tags`、`projects`、`settings`、`system`、`home`、`oauth`。
- [x] 4.4 `router/`：vue-router 4 + 14 条路由，全局 beforeEach 检查 `auth.isLoggedIn`，afterEach 把路由写入 tab store。

## 5. 业务页面

- [x] 5.1 登录页：紫蓝渐变 + 卡片 + 8 位密码校验。
- [x] 5.2 默认布局：Sider（左侧菜单）+ Header（搜索 + 语言 + 主题 + 用户菜单）+ TabBar + Content。
- [x] 5.3 仪表盘：4 张渐变统计卡 + 顶部欢迎横幅 + ECharts 折线区域图（最近 14 天）+ 圆环图（账号类型）+ 4 张快捷链接卡。
- [x] 5.4 邮箱视图：按 provider 分类的左栏 + 个人常用 + 账号 + 邮件列表 + 详情；支持 inbox/junk/deleted/all 切换、批量标记已读 / 删除。
- [x] 5.5 账号管理：NDataTable + 关键词 / 分组 / 类型过滤 + 类型标签 + 标签 chip + 单 / 批量删除 + 批量标签 / 移动分组 / 开关转发 + 导出对话框。
- [x] 5.6 内网邮箱页：账号列表 + 顶级 🎲 随机生成按钮（域名 dropdown，前缀长度 10 固定）+ 添加按钮 + 复制邮箱 + 删除 + 邮件列表 + 详情。
- [x] 5.7 临时邮箱页：3 provider tab + 列表 + 生成对话框 + 批量删除。
- [x] 5.8 Token 刷新页：NDataTable + 选中刷新 SSE + 失败重试流式 + 实时进度条 + 事件日志。
- [x] 5.9 邮件转发设置：4 张卡（常规 / SMTP / Telegram / WeCom）+ 测试发送 + 立即触发。
- [x] 5.10 转发历史页：全部 / 失败 2 tab。
- [x] 5.11 WebDAV 备份：Cron 预览 + 测试连接 + 手动上传（密码确认）。
- [x] 5.12 标签管理：8 色预设 + 取色器 + CRUD。
- [x] 5.13 项目（Projects）：项目下拉 + 启动 / 领取 / 完成 / 释放 / 重置 / 移除。
- [x] 5.14 审计日志页：分页 + 关键词 / 动作 / 资源类型过滤。
- [x] 5.15 Docker 在线更新页：状态 descriptions + 触发更新 + 3s 轮询。
- [x] 5.16 设置页：4 tab（常规 / 安全 / 对外 API / 高级 DuckMail+Cloudflare+时区）。
- [x] 5.17 全局搜索（Ctrl/Cmd+K）：debounced 输入 + 类型路由跳转。
- [x] 5.18 账号编辑抽屉：凭据 / 标签 / 别名 / 转发开关 / 状态 / 分组（含 internal_eml 分支）。

## 6. XSS 净化

- [x] 6.1 引入 `dompurify@3.0.8`，新建 `web/src/utils/sanitize.ts`，禁用 script/style/iframe/object/embed/form + 剥离 `on*` 事件 + 强制 `target=_blank rel=noopener`。
- [x] 6.2 `mailbox`、`internal-eml`、`temp-emails` 三处 v-html 渲染前调用 `sanitizeEmailHtml`。

## 7. 部署链路

- [x] 7.1 `Dockerfile` 改多阶段：stage 1 `node:20-alpine` 跑 `npm install && npm run build`；stage 2 `python:3.11-slim` 复制 `/web/dist`。
- [x] 7.2 `.dockerignore` 排除 `web/node_modules`、`web/dist`、`web/.vite`。
- [x] 7.3 `.github/workflows/release.yml`：PyInstaller 步骤前增加 `actions/setup-node@v4` + `npm install --no-audit --no-fund` + `npm run build`。
- [x] 7.4 `outlookEmail.spec`：检测 `web/dist` 存在时把它加入 `datas`。
- [x] 7.5 文档：新增 `docs/deploy-mac-lan.md`（局域网 Mac 部署 + Windows 浏览器访问）。

## 8. 测试与验收

- [x] 8.1 调整 `tests/test_imap_folder_resolution.py::AssetRenderingTests`：测 SPA shell 或 fallback、catch-all 路径。
- [x] 8.2 `pytest tests/test_*.py` 单文件运行：152 passed / 1 pre-existing fail（与本次无关）。
- [x] 8.3 vue-tsc 通过；`npm run build` 通过。
- [x] 8.4 端到端冒烟：登录、SPA shell、Vite 资源命中、API 鉴权、catch-all、404 不再被错误处理器吞成 500。
- [x] 8.5 真实 Flask 服务（绑定 0.0.0.0:5050）+ curl 全链路验证。

## 9. 修复（dev-vue 自审计后）

- [x] 9.1 `api_update_account` 与 `api_update_account_v2` 都增加 `is_internal_eml` 分支（修复前 PUT 会把 internal_eml 降级为 imap+custom）。
- [x] 9.2 `08_forwarding_scheduler_errors.py` 调度器 SQL 加 `AND account_type != 'internal_eml'`（避免空 Graph 凭据刷屏）。
- [x] 9.3 axios 拦截器：CSRF 400/403 失败时拉新 token 并重放一次（带 `_csrfRetried` 防循环）；处理 `csrf_disabled=true`。
- [x] 9.4 `AccountEditDrawer.save()`：diff `aliasesText` 并随 PUT 提交，避免用户切换主表单 / 别名表单时丢失编辑。
- [x] 9.5 `mailbox.batchDelete`：在清空 `checked` 之前先记录 deleted set，确保删除集合包含当前详情时正确清空详情面板。
- [x] 9.6 `templates/index.html` 直接 link 8 个 `static/css/index/*.css`，移除被删除的 `bundled_index_css` 引用，回退路径不再 500。
