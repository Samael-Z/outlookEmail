# Mac 局域网部署 + Windows 远程访问指南

> 目标：把 `dev-vue` 分支跑在一台 Mac 上，让同一局域网内的 Windows 浏览器
> 通过 `http://<mac-ip>:5000` 访问完整管理界面。

## 一、推荐方案：Docker（一行起服务）

### 1. 准备 Mac

```bash
# 安装 Docker Desktop for Mac（已装跳过）
brew install --cask docker
open -a Docker   # 等 Docker 图标变成"运行中"

# 克隆代码
git clone -b dev-vue https://github.com/Samael-Z/outlookEmail.git
cd outlookEmail
```

### 2. 用 docker compose 跑

在仓库根目录新建 `docker-compose.lan.yml`：

```yaml
services:
  outlook-mail-reader:
    build: .                        # 多阶段 Dockerfile，会自动跑 npm build + Flask
    container_name: outlook-mail-reader
    ports:
      - "0.0.0.0:5000:5000"         # 0.0.0.0 = 监听所有网卡，局域网才能访问
    volumes:
      - ./data:/app/data            # 持久化 SQLite + secret_key
    environment:
      - LOGIN_PASSWORD=admin123     # 第一次启动会用这个值哈希；之后改成强密码
      - SECRET_KEY=换成 64 位随机串
      - FLASK_ENV=production
      # 内网 EML 邮件服务器（可选；不填则用代码内置的默认表）
      # - INTERNAL_EML_CS2JP_COM_BASEURL=http://cs-email-manager.17usoft.com
      # - INTERNAL_EML_JOKERQUE_COM_BASEURL=http://mail.jokerque.com:8080
      # - INTERNAL_EML_API_KEY=eml_server_private_KEY_2023
    restart: unless-stopped
```

启动：

```bash
# 生成 SECRET_KEY，替换上面的占位
python3 -c "import secrets; print(secrets.token_hex(32))"

docker compose -f docker-compose.lan.yml up -d --build
docker logs -f outlook-mail-reader   # 看启动日志
```

构建过程：

1. Stage 1 `node:20-alpine` 跑 `npm install + npm run build` 生成 `web/dist/`
2. Stage 2 `python:3.11-slim` 装 Python 依赖 + 拷贝 dist，单 worker gunicorn

镜像首次构建 5–8 分钟，之后只重启秒级。

### 3. 拿 Mac 的局域网 IP

```bash
# Mac 上
ipconfig getifaddr en0   # Wi-Fi
# 或
ipconfig getifaddr en1   # 有线
```

假设输出 `192.168.1.42`。

### 4. Mac 开放防火墙

`系统设置 → 网络 → 防火墙 → 选项`，确保 Docker 被允许接受入站连接。
如果防火墙关着可以跳过。

### 5. Windows 浏览器访问

```
http://192.168.1.42:5000
```

第一次登录密码 `admin123`，进去后立刻到 **设置 → 安全 → 修改密码** 改成强密码。

### 6. 测试内网邮箱接入

- 账号管理 → 添加账号 → "内网 EML" tab
- 输入 `test@cs2jp.com` 或 `test@jokerque.com`
- 自动识别 baseURL，留空 API Key 使用默认密钥
- 创建后到"内网邮箱"页点"拉取"测试连通性

## 二、备用方案：Python 直接跑（不用 Docker）

适用于不想装 Docker 的场景。

```bash
# Mac 上
brew install python@3.12 node@20
git clone -b dev-vue https://github.com/Samael-Z/outlookEmail.git
cd outlookEmail

# 1. 装 Python 依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. 构建前端
cd web
npm install
npm run build
cd ..

# 3. 启动（监听所有网卡，让 Windows 能访问）
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
export HOST=0.0.0.0
export PORT=5000
python3 web_outlook_app.py
```

后台运行（关闭终端不退出）：

```bash
nohup python3 web_outlook_app.py > app.log 2>&1 &
```

访问方式同上：`http://<mac-ip>:5000`

## 三、开发模式（双端口热重载，可选）

如果你要在 Windows 上改 Vue 代码并即时看到 Mac 的效果（罕见用法）：

```bash
# Mac 上启 Flask（端口 5000）
python3 web_outlook_app.py

# Mac 上另起 Vite dev server（端口 5173，开放到局域网）
cd web
npm run dev -- --host 0.0.0.0
```

Windows 上访问 `http://<mac-ip>:5173`，Vite 会把 `/api` 代理到 `127.0.0.1:5000`。
这种模式只适合开发，生产用方案一。

## 四、常见问题

### Windows 访问超时

1. **检查端口监听**：Mac 上 `lsof -iTCP -sTCP:LISTEN | grep 5000`，必须看到 `*:5000` 或 `0.0.0.0:5000` 而不是 `127.0.0.1:5000`。
2. **Mac 防火墙**：临时关掉测试 `sudo pfctl -d`，验证后再开 `sudo pfctl -e` 并加规则。
3. **同一网段**：`ping <mac-ip>` 应该通。Wi-Fi 隔离（AP isolation）会阻断设备互访。
4. **代理污染**：Windows 上检查 IE 代理设置，公司 VPN 客户端常截获 5000 端口。

### 内网 EML 服务器在 Mac 上访问不到

```bash
docker exec outlook-mail-reader curl -v http://mail.jokerque.com:8080
```

如果 Mac 本身能 ping 通但容器内不能，是 Docker 网络问题，把容器换成 `network_mode: host`（仅 Linux/Mac，Windows Docker 不支持）。

### Token 刷新 SSE 流式进度不显示

后端必须以 **单 worker** 运行（默认就是）；如果你自己改了 gunicorn workers > 1 会导致 SSE 订阅命中不到任务进程。

### 重置登录密码

停止容器后删除 `data/outlook_accounts.db` 里的密码 setting：

```bash
docker compose -f docker-compose.lan.yml stop
sqlite3 data/outlook_accounts.db "DELETE FROM settings WHERE key='login_password';"
docker compose -f docker-compose.lan.yml start
```

下次登录用 `LOGIN_PASSWORD` 环境变量里的值。

## 五、把 Mac 配成 Bonjour 主机名（可选）

懒得记 IP 可以用 mDNS：

```bash
# Mac 上看主机名
hostname  # 假设输出 macbook-pro.local
```

Windows 10/11 装好 iTunes（或 Bonjour Print Services）后可以直接：

```
http://macbook-pro.local:5000
```

## 六、安全建议

- ✅ 修改默认登录密码（设置 → 安全 → 修改密码，≥ 8 位）
- ✅ 内网邮箱 baseURL 不要暴露在公网；通过 VPN 访问
- ✅ 不要把 `data/` 目录直接对外暴露（含明文 SECRET_KEY 与 SQLite）
- ✅ 如果要从外网访问，前面套 Caddy/Nginx 反向代理 + HTTPS + 基础认证
- ⚠️ 当前 `InternalEmlClient` 走 HTTP（明文）—— 内网用没问题，跨网段慎用
