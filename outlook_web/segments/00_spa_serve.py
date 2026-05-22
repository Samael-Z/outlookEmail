"""SPA 服务层：提供 Vue 构建产物 dist/ 的静态资源服务与 SPA 入口回退。

加载顺序：本 segment 必须最先加载（编号 00），因为它定义了 `_serve_spa_or_fallback`
这个工具函数，会被 segment 04 的 `/`、`/login` 等路由用到。
catch-all 路由 `/<path:path>` 必须最后注册（在 segment 11 中），否则会
优先匹配掉后续才会注册的 API 路由。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from web_outlook_app import *  # noqa: F403


# ==================== 解析 web/dist 路径 ====================

def _resolve_web_dist() -> Path:
    """解析 web/dist 目录，覆盖三种部署形态：
    - Python 直跑：项目根 web/dist
    - PyInstaller exe：_MEIPASS/web/dist
    - Docker：/app/web/dist
    支持环境变量 WEB_DIST_DIR 覆盖。
    """
    override = os.getenv('WEB_DIST_DIR')
    if override:
        return Path(override)
    return resource_path('web', 'dist')


WEB_DIST_DIR: Path = _resolve_web_dist()
WEB_DIST_INDEX: Path = WEB_DIST_DIR / 'index.html'
WEB_DIST_ASSETS: Path = WEB_DIST_DIR / 'assets'


def has_spa_build() -> bool:
    return WEB_DIST_INDEX.is_file()


def _serve_spa_or_fallback(fallback_template: str, template_context: Optional[dict] = None):
    """SPA 优先；不存在时回退到旧 Jinja 模板。"""
    if has_spa_build():
        return send_from_directory(str(WEB_DIST_DIR), 'index.html')
    return render_template(fallback_template, **(template_context or {}))


# 把 send_from_directory 暴露到全局，方便其他 segment 引用
from flask import send_from_directory  # noqa: E402
