# ============================================================
# Stage 1: 构建 Vue 前端
# ============================================================
FROM node:20-alpine AS web-builder
WORKDIR /web

# 先拷依赖文件，最大化 layer 缓存命中率
COPY web/package.json web/package-lock.json* ./
RUN npm install --no-audit --no-fund --loglevel=error

# 拷贝源码并构建
COPY web/ ./
RUN npm run build

# ============================================================
# Stage 2: Python 运行时
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# 安装 curl（用于健康检查）
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    GUNICORN_TIMEOUT=300 \
    GUNICORN_THREADS=4 \
    IMAP_TIMEOUT=45

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn

# 拷贝应用代码（排除 web/ 通过 .dockerignore 单独处理）
COPY . .

# 从构建阶段拷贝 Vue 构建产物，覆盖 web/ 目录里可能存在的源码
RUN rm -rf /app/web/node_modules /app/web/src /app/web/dist
COPY --from=web-builder /web/dist /app/web/dist

# 创建数据目录
RUN mkdir -p /app/data

EXPOSE 5000

# 启动：单 worker + 多线程（Token 刷新 SSE 依赖进程内状态）
CMD ["sh", "-c", "gunicorn -k gthread -w 1 --threads ${GUNICORN_THREADS:-4} -b 0.0.0.0:5000 --timeout ${GUNICORN_TIMEOUT:-300} --graceful-timeout 30 --access-logfile - --error-logfile - --capture-output web_outlook_app:app"]
