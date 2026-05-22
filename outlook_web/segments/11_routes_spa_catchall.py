"""SPA catch-all 路由：必须在所有 API 路由之后注册（编号 11，最后加载）。

提供：
- `/assets/<path:filename>`  →  返回 web/dist/assets/<filename>（Vue 构建出的 JS/CSS）
- `/<path:path>`             →  返回 web/dist/index.html（让 Vue Router 接管前端路由）
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from flask import abort, send_from_directory

if TYPE_CHECKING:
    from web_outlook_app import *  # noqa: F403


@app.route('/assets/<path:filename>')
def spa_assets(filename):
    """Vue 构建产物 dist/assets/ 静态服务"""
    if not has_spa_build():
        abort(404)
    full = WEB_DIST_ASSETS / filename
    # 防御性：禁止越级访问
    try:
        full.resolve().relative_to(WEB_DIST_ASSETS.resolve())
    except ValueError:
        abort(403)
    if not full.is_file():
        abort(404)
    return send_from_directory(str(WEB_DIST_ASSETS), filename)


# Vite 默认会在 dist 根目录放一些非 assets 文件（如 favicon、manifest）
# 这里同时支持 dist 根目录下的其他静态文件
_DIST_ROOT_STATIC_FILES = {'manifest.webmanifest', 'robots.txt', 'sitemap.xml'}


@app.route('/<path:path>')
def spa_catch_all(path):
    """所有未被前面注册的路由匹配的请求，统一返回 SPA index.html。

    例外：
    - /api/* 已经在前面注册，自然不会进到这里
    - /favicon.ico 已经在 segment 04 注册
    - 显式拒绝 /static/* 路径（旧资源），避免误命中
    """
    # 显式拒绝可能错误命中的旧 static 路径
    if path.startswith('static/') or path.startswith('api/'):
        abort(404)

    # 允许根目录下的少量静态文件（manifest 等）
    base = path.split('/', 1)[0]
    if base in _DIST_ROOT_STATIC_FILES and has_spa_build():
        full = WEB_DIST_DIR / path
        if full.is_file():
            return send_from_directory(str(WEB_DIST_DIR), path)

    # 默认：返回 SPA 入口，由 Vue Router 处理前端路由
    if has_spa_build():
        return send_from_directory(str(WEB_DIST_DIR), 'index.html')
    abort(404)
