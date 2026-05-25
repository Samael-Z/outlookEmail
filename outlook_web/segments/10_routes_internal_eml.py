from __future__ import annotations

import hashlib
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from web_outlook_app import *  # noqa: F403


# ==================== 内网 EML 邮件服务器：配置 ====================

INTERNAL_EML_DOMAIN_BASEURL_DEFAULT: Dict[str, str] = {
    'cs2jp.com': 'http://cs-email-manager.17usoft.com',
    'jokerque.com': 'http://mail.jokerque.com:8080',
}
INTERNAL_EML_DEFAULT_KEY = 'eml_server_private_KEY_2023'
INTERNAL_EML_MAX_FETCH_PER_REFRESH = 200  # 单账号单次刷新最多拉取邮件数


def get_internal_eml_baseurl_for_domain(domain: str) -> Optional[str]:
    """根据邮箱域名解析 baseURL：环境变量优先 > 内置默认表"""
    if not domain:
        return None
    env_key = 'INTERNAL_EML_' + domain.upper().replace('.', '_').replace('-', '_') + '_BASEURL'
    return os.getenv(env_key) or INTERNAL_EML_DOMAIN_BASEURL_DEFAULT.get(domain.lower())


def get_internal_eml_default_key() -> str:
    return os.getenv('INTERNAL_EML_API_KEY', INTERNAL_EML_DEFAULT_KEY)


# ==================== InternalEmlClient ====================

class InternalEmlClient:
    """对接内网 EML 邮件服务器的 HTTP 客户端。

    协议：
      - GET /download?timestamp=&signature=                   拉队列下一封
      - GET /get?timestamp=&signature=&email=<addr>           按收件人拉指定邮件
      - GET /delete?timestamp=&signature=&filename=<name>     按文件名删除
    签名：md5(timestamp + privateKey + suffix)，suffix 因端点而异。
    服务端"无邮件"时响应体是字面量 b"EMPTY"。
    """

    def __init__(self, base_url: str, private_key: str, proxies: Optional[Dict[str, str]] = None,
                 timeout: int = 30, verify_tls: Optional[bool] = None):
        self.base_url = (base_url or '').rstrip('/')
        self.private_key = private_key or ''
        self.proxies = proxies
        self.timeout = timeout
        # verify_tls 三态：
        #   None  → 按 scheme 推断（http=False / https=True）
        #   True  → 显式开启证书校验
        #   False → 显式关闭（用于内网自签证书；通过 INTERNAL_EML_INSECURE 触发）
        if verify_tls is None:
            self.verify_tls = self.base_url.lower().startswith('https://')
        else:
            self.verify_tls = bool(verify_tls)

    def _sign(self, suffix: str) -> Tuple[str, str]:
        ts = str(int(time.time()))
        sig = hashlib.md5((ts + self.private_key + suffix).encode('utf-8')).hexdigest()
        return ts, sig

    def _is_empty(self, body: bytes) -> bool:
        """服务端无邮件时返回 b'EMPTY'（可能带尾部空白）。
        精确匹配 strip 后的值，避免任何以 'EMPTY' 开头的真实 EML 被误判。
        """
        if not body:
            return False
        return body.strip() == b'EMPTY'

    def get_email(self, email_addr: str) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
        """按收件人拉指定邮件。返回 (content, filename, error)。
        无邮件时 content/filename 都为 None 且 error 为 None。
        """
        ts, sig = self._sign(email_addr)
        params = {'timestamp': ts, 'signature': sig, 'email': email_addr}
        try:
            r = requests.get(f'{self.base_url}/get', params=params,
                             proxies=self.proxies, timeout=self.timeout, verify=self.verify_tls)
        except Exception as exc:
            return None, None, f'request error: {exc}'
        if r.status_code != 200:
            return None, None, f'HTTP {r.status_code}: {r.text[:200]}'
        if self._is_empty(r.content):
            return None, None, None
        filename = _extract_filename(r.headers.get('Content-Disposition', ''))
        return r.content, filename, None

    def download_next(self) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
        """拉队列下一封邮件（不指定收件人）。"""
        ts, sig = self._sign('')
        params = {'timestamp': ts, 'signature': sig}
        try:
            r = requests.get(f'{self.base_url}/download', params=params,
                             proxies=self.proxies, timeout=self.timeout, verify=self.verify_tls)
        except Exception as exc:
            return None, None, f'request error: {exc}'
        if r.status_code != 200:
            return None, None, f'HTTP {r.status_code}: {r.text[:200]}'
        if self._is_empty(r.content):
            return None, None, None
        filename = _extract_filename(r.headers.get('Content-Disposition', ''))
        return r.content, filename, None

    def delete(self, filename: str) -> Tuple[bool, Optional[str]]:
        if not filename:
            return False, 'empty filename'
        ts, sig = self._sign(filename)
        params = {'timestamp': ts, 'signature': sig, 'filename': filename}
        try:
            r = requests.get(f'{self.base_url}/delete', params=params,
                             proxies=self.proxies, timeout=self.timeout, verify=self.verify_tls)
        except Exception as exc:
            return False, f'request error: {exc}'
        if r.status_code == 200:
            return True, None
        return False, f'HTTP {r.status_code}: {r.text[:200]}'


def _extract_filename(content_disposition: str) -> str:
    """解析 Content-Disposition 的 filename，兼容 RFC 5987 的 filename*= 形式。

    - filename="foo.eml"
    - filename=foo.eml
    - filename*=UTF-8''foo.eml （优先采用，RFC 5987）
    """
    if not content_disposition:
        return ''

    import re
    from urllib.parse import unquote

    # RFC 5987: filename*=<charset>'<lang>'<percent-encoded>
    m = re.search(r"filename\*\s*=\s*([^']*)'[^']*'([^;]+)", content_disposition, re.IGNORECASE)
    if m:
        charset = (m.group(1) or 'utf-8').strip() or 'utf-8'
        try:
            return unquote(m.group(2).strip(), encoding=charset, errors='replace')
        except (LookupError, TypeError):
            return unquote(m.group(2).strip())

    # 经典 filename=
    m = re.search(r'filename\s*=\s*"([^"]*)"', content_disposition, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r'filename\s*=\s*([^;]+)', content_disposition, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    return ''


# ==================== EML 解析 ====================

def parse_eml_bytes(content: bytes) -> Dict[str, Any]:
    msg = BytesParser(policy=policy.default).parsebytes(content)

    text_body = ''
    html_body = ''
    try:
        part = msg.get_body(preferencelist=('plain',))
        if part is not None:
            text_body = part.get_content()
    except Exception:
        pass
    try:
        part = msg.get_body(preferencelist=('html',))
        if part is not None:
            html_body = part.get_content()
    except Exception:
        pass

    attachments: List[Dict[str, Any]] = []
    try:
        for p in msg.iter_attachments():
            payload = p.get_payload(decode=True) or b''
            attachments.append({
                'filename': p.get_filename() or '',
                'content_type': p.get_content_type(),
                'size': len(payload),
            })
    except Exception:
        pass

    return {
        'subject': str(msg['Subject'] or ''),
        'from': str(msg['From'] or ''),
        'to': str(msg['To'] or ''),
        'date': str(msg['Date'] or ''),
        'text': text_body,
        'html': html_body,
        'attachments': attachments,
    }


# ==================== 数据库 schema 初始化 ====================

def ensure_internal_eml_schema() -> None:
    conn = sqlite3.connect(DATABASE)
    try:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS internal_eml_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                server_filename TEXT NOT NULL,
                subject TEXT,
                from_addr TEXT,
                to_addr TEXT,
                body_text TEXT,
                body_html TEXT,
                has_attachment INTEGER DEFAULT 0,
                raw_eml BLOB,
                received_at TIMESTAMP,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
            )
        ''')
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_iem_account_received
            ON internal_eml_messages(account_id, received_at DESC)
        ''')
        cur.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_iem_account_filename
            ON internal_eml_messages(account_id, server_filename)
        ''')
        conn.commit()
    finally:
        conn.close()


try:
    ensure_internal_eml_schema()
except Exception as _exc:
    print(f'[internal_eml] schema init warning: {_exc}')


# ==================== 业务 helper ====================

def _domain_from_email(email_addr: str) -> str:
    if email_addr and '@' in email_addr:
        return email_addr.rsplit('@', 1)[1].lower()
    return ''


def _build_client_for_account(account: Dict[str, Any]) -> Optional[InternalEmlClient]:
    base_url = (account.get('imap_host') or '').strip()
    if not base_url:
        domain = _domain_from_email(account.get('email', ''))
        base_url = get_internal_eml_baseurl_for_domain(domain) or ''
    if not base_url:
        return None

    # imap_password 已在写入时通过 encrypt_data 加密；读取路径用 decrypt_data 还原
    raw_key = (account.get('imap_password') or '').strip()
    private_key = decrypt_data(raw_key) if raw_key else ''
    if not private_key:
        private_key = get_internal_eml_default_key()

    # 环境变量 INTERNAL_EML_INSECURE=true 显式跳过 TLS 校验（自签证书场景）
    insecure_env = (os.getenv('INTERNAL_EML_INSECURE', '') or '').strip().lower()
    verify_tls: Optional[bool] = False if insecure_env in {'1', 'true', 'yes', 'on'} else None

    proxies: Optional[Dict[str, str]] = None
    group_id = account.get('group_id')
    if group_id:
        conn = None
        try:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            grow = conn.execute('SELECT proxy_url FROM groups WHERE id = ?', (group_id,)).fetchone()
            if grow:
                purl = (grow['proxy_url'] or '').strip()
                if purl:
                    proxies = {'http': purl, 'https': purl}
        except Exception:
            pass
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    return InternalEmlClient(base_url, private_key, proxies=proxies, verify_tls=verify_tls)


def _fetch_internal_eml_account(account_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db()
    row = conn.execute(
        'SELECT * FROM accounts WHERE id = ? AND account_type = ?',
        (account_id, 'internal_eml')
    ).fetchone()
    if not row:
        return None
    account = dict(row)
    # 还原加密字段，便于后续 _build_client_for_account 直接使用
    if account.get('imap_password'):
        account['imap_password'] = decrypt_data(account['imap_password'])
    return account


def fetch_and_store_internal_eml(account: Dict[str, Any]) -> Tuple[int, int, Optional[str]]:
    """从内网服务器拉取本账号的全部待消费邮件，落库后再删服务端。

    返回 (fetched, deleted, error_msg)。
    """
    client = _build_client_for_account(account)
    if client is None:
        return 0, 0, '无法解析 baseURL（请检查域名或自定义 baseURL）'

    fetched = 0
    deleted = 0
    error: Optional[str] = None

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        for _ in range(INTERNAL_EML_MAX_FETCH_PER_REFRESH):
            content, filename, err = client.get_email(account['email'])
            if err:
                error = err
                break
            if content is None:
                break  # 服务端队列为空

            try:
                parsed = parse_eml_bytes(content)
            except Exception as exc:
                error = f'EML 解析失败: {exc}'
                break

            received_iso: Optional[str] = None
            date_str = parsed.get('date', '')
            if date_str:
                try:
                    received_iso = parsedate_to_datetime(date_str).isoformat()
                except Exception:
                    received_iso = None

            try:
                conn.execute('''
                    INSERT OR IGNORE INTO internal_eml_messages
                    (account_id, email, server_filename, subject, from_addr, to_addr,
                     body_text, body_html, has_attachment, raw_eml, received_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    account['id'],
                    account['email'],
                    filename or '',
                    parsed.get('subject', ''),
                    parsed.get('from', ''),
                    parsed.get('to', ''),
                    parsed.get('text', '')[:200_000],
                    parsed.get('html', '')[:500_000],
                    1 if parsed.get('attachments') else 0,
                    content,
                    received_iso,
                ))
                conn.commit()
                fetched += 1
            except Exception as exc:
                error = f'落库失败（未删除服务端文件）: {exc}'
                break

            # 关键：落库成功才删服务端
            if filename:
                ok, derr = client.delete(filename)
                if ok:
                    deleted += 1
                else:
                    # 单次 delete 失败不再中断整轮 drain：累计错误后继续，
                    # 让其余排队邮件也能被消费；下一轮再尝试删除（INSERT OR IGNORE 已经去重）。
                    last_err = f'服务端删除失败 {filename}: {derr}'
                    error = last_err if error is None else f'{error}; {last_err}'
                    continue
            else:
                # 缺失 Content-Disposition filename 时无法删除，记录但继续
                last_err = '响应缺少 Content-Disposition filename，跳过删除'
                error = last_err if error is None else f'{error}; {last_err}'
                continue
    finally:
        conn.close()

    return fetched, deleted, error


# ==================== HTTP 路由 ====================

@app.route('/api/home/stats', methods=['GET'])
@login_required
def api_home_stats():
    """首页仪表盘聚合统计：账号汇总 + 内网邮件最近 14 天入库曲线 + 刷新成功率。"""
    db = get_db()

    row_totals = db.execute('''
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN account_type = 'outlook' THEN 1 ELSE 0 END) AS outlook,
            SUM(CASE WHEN account_type = 'imap' THEN 1 ELSE 0 END) AS imap,
            SUM(CASE WHEN account_type = 'internal_eml' THEN 1 ELSE 0 END) AS internal_eml,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN forward_enabled = 1 THEN 1 ELSE 0 END) AS forwarding
        FROM accounts
    ''').fetchone()

    groups_count = db.execute('SELECT COUNT(*) AS c FROM groups').fetchone()['c']
    temp_count = db.execute('SELECT COUNT(*) AS c FROM temp_emails').fetchone()['c']

    # 内网邮件最近 14 天每日入库数
    try:
        daily = db.execute('''
            SELECT DATE(fetched_at) AS d, COUNT(*) AS c
            FROM internal_eml_messages
            WHERE fetched_at >= datetime('now', '-13 days')
            GROUP BY DATE(fetched_at)
            ORDER BY d
        ''').fetchall()
        daily_map = {r['d']: r['c'] for r in daily}
    except Exception:
        daily_map = {}

    from datetime import date, timedelta
    today = date.today()
    series = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        key = d.isoformat()
        series.append({'date': key, 'count': daily_map.get(key, 0)})

    # 最近 7 天 Token 刷新成功 / 失败
    try:
        refresh_rows = db.execute('''
            SELECT status, COUNT(*) AS c
            FROM account_refresh_logs
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY status
        ''').fetchall()
        refresh_stats = {r['status']: r['c'] for r in refresh_rows}
    except Exception:
        refresh_stats = {}

    return jsonify({
        'success': True,
        'totals': {
            'accounts': row_totals['total'] or 0,
            'outlook': row_totals['outlook'] or 0,
            'imap': row_totals['imap'] or 0,
            'internal_eml': row_totals['internal_eml'] or 0,
            'active': row_totals['active'] or 0,
            'forwarding': row_totals['forwarding'] or 0,
            'groups': groups_count,
            'temp_emails': temp_count,
        },
        'internal_eml_daily': series,
        'refresh_recent': {
            'success': refresh_stats.get('success', 0),
            'failed': refresh_stats.get('failed', 0),
        },
    })


@app.route('/api/internal-eml/config/domains', methods=['GET'])
@login_required
def api_internal_eml_domains():
    """返回域名 → baseURL 映射，给前端账号导入弹窗用。"""
    domains = {}
    for d in INTERNAL_EML_DOMAIN_BASEURL_DEFAULT:
        domains[d] = get_internal_eml_baseurl_for_domain(d)
    return jsonify({
        'success': True,
        'domains': domains,
        'default_key': get_internal_eml_default_key(),
        'default_key_present': bool(get_internal_eml_default_key()),
    })


@app.route('/api/internal-eml/accounts', methods=['POST'])
@login_required
def api_internal_eml_create_account():
    """创建一个内网 EML 邮箱账号。

    body: { email, api_key?, base_url?, group_id?, remark? }
    """
    data = request.get_json(silent=True) or {}
    email_addr = (data.get('email') or '').strip()
    if not email_addr or '@' not in email_addr:
        return jsonify({'success': False, 'error': '邮箱地址不能为空且必须包含 @'}), 400

    domain = _domain_from_email(email_addr)
    base_url = (data.get('base_url') or '').strip()
    if not base_url:
        base_url = get_internal_eml_baseurl_for_domain(domain) or ''
    if not base_url:
        return jsonify({
            'success': False,
            'error': f'域名 {domain} 没有内置 baseURL，请显式提供 base_url 或配置环境变量'
        }), 400

    api_key = (data.get('api_key') or '').strip() or get_internal_eml_default_key()
    group_id = data.get('group_id')
    try:
        group_id = int(group_id) if group_id is not None else None
    except (TypeError, ValueError):
        group_id = None
    if group_id is None:
        # 默认放到第一个非临时邮箱分组
        conn = get_db()
        row = conn.execute(
            "SELECT id FROM groups WHERE name != '临时邮箱' ORDER BY sort_order, id LIMIT 1"
        ).fetchone()
        group_id = row['id'] if row else 1

    remark = (data.get('remark') or '').strip()[:500]

    conn = sqlite3.connect(DATABASE)
    try:
        cur = conn.cursor()
        # 检查重复
        existing = cur.execute('SELECT id FROM accounts WHERE email = ?', (email_addr,)).fetchone()
        if existing:
            return jsonify({'success': False, 'error': f'邮箱 {email_addr} 已存在'}), 409
        encrypted_api_key = encrypt_data(api_key) if api_key else api_key
        cur.execute('''
            INSERT INTO accounts
            (email, password, client_id, refresh_token, group_id, sort_order, remark,
             status, account_type, provider, imap_host, imap_port, imap_password,
             forward_enabled, created_at, updated_at)
            VALUES (?, '', '', '', ?, 0, ?, 'active', 'internal_eml', 'internal_eml',
                    ?, 0, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (email_addr, group_id, remark, base_url, encrypted_api_key))
        account_id = cur.lastrowid
        conn.commit()
    except Exception as exc:
        return jsonify({'success': False, 'error': f'创建失败: {exc}'}), 500
    finally:
        conn.close()

    return jsonify({
        'success': True,
        'account': {
            'id': account_id,
            'email': email_addr,
            'account_type': 'internal_eml',
            'provider': 'internal_eml',
            'imap_host': base_url,
            'group_id': group_id,
            'remark': remark,
        },
    })


@app.route('/api/internal-eml/accounts/generate-random', methods=['POST'])
@login_required
def api_internal_eml_generate_random():
    """随机生成一个内网 EML 邮箱地址并直接创建账号。

    body: { domain?: 'cs2jp.com' | 'jokerque.com', prefix_length?: 8, group_id?, remark? }
    返回 { success, account: {id, email, base_url, ...} }
    """
    import secrets as _secrets
    import string as _string

    data = request.get_json(silent=True) or {}

    # 1) 选择域名
    domain = (data.get('domain') or '').strip().lower()
    if not domain:
        # 没指定就随便挑一个支持的
        domains = list(INTERNAL_EML_DOMAIN_BASEURL_DEFAULT.keys())
        if not domains:
            return jsonify({'success': False, 'error': '没有可用的内网域名'}), 400
        domain = _secrets.choice(domains)
    elif domain not in INTERNAL_EML_DOMAIN_BASEURL_DEFAULT and \
            not get_internal_eml_baseurl_for_domain(domain):
        return jsonify({'success': False, 'error': f'不支持的域名: {domain}'}), 400

    base_url = get_internal_eml_baseurl_for_domain(domain) or ''
    if not base_url:
        return jsonify({'success': False, 'error': f'域名 {domain} 无法解析 baseURL'}), 400

    # 2) 前缀生成（默认 10 字符 [a-z0-9]，避免名称冲突时最多重试 5 次）
    try:
        prefix_length = max(4, min(32, int(data.get('prefix_length') or 10)))
    except (TypeError, ValueError):
        prefix_length = 10

    alphabet = _string.ascii_lowercase + _string.digits

    api_key = get_internal_eml_default_key()
    encrypted_api_key = encrypt_data(api_key) if api_key else api_key

    group_id = data.get('group_id')
    try:
        group_id = int(group_id) if group_id is not None else None
    except (TypeError, ValueError):
        group_id = None

    remark = (data.get('remark') or '随机生成').strip()[:500]

    conn = sqlite3.connect(DATABASE)
    try:
        cur = conn.cursor()
        if group_id is None:
            row = cur.execute(
                "SELECT id FROM groups WHERE name != '临时邮箱' ORDER BY sort_order, id LIMIT 1"
            ).fetchone()
            group_id = row[0] if row else 1

        last_err = ''
        for _ in range(5):
            prefix = ''.join(_secrets.choice(alphabet) for _ in range(prefix_length))
            email_addr = f'{prefix}@{domain}'
            existing = cur.execute('SELECT id FROM accounts WHERE email = ?', (email_addr,)).fetchone()
            if existing:
                last_err = f'冲突: {email_addr} 已存在'
                continue
            try:
                cur.execute('''
                    INSERT INTO accounts
                    (email, password, client_id, refresh_token, group_id, sort_order, remark,
                     status, account_type, provider, imap_host, imap_port, imap_password,
                     forward_enabled, created_at, updated_at)
                    VALUES (?, '', '', '', ?, 0, ?, 'active', 'internal_eml', 'internal_eml',
                            ?, 0, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (email_addr, group_id, remark, base_url, encrypted_api_key))
                account_id = cur.lastrowid
                conn.commit()
                return jsonify({
                    'success': True,
                    'account': {
                        'id': account_id,
                        'email': email_addr,
                        'domain': domain,
                        'base_url': base_url,
                        'group_id': group_id,
                        'remark': remark,
                    },
                })
            except Exception as exc:
                last_err = str(exc)
                continue
        return jsonify({'success': False, 'error': f'生成失败: {last_err or "未知错误"}'}), 500
    finally:
        conn.close()


@app.route('/api/internal-eml/accounts/bulk', methods=['POST'])
@login_required
def api_internal_eml_bulk_create():
    """批量创建内网 EML 账号。

    body: { items: [{ email, api_key?, base_url? }, ...], group_id?, remark? }
    返回每行的创建结果，跳过已存在的邮箱。
    """
    data = request.get_json(silent=True) or {}
    items = data.get('items') or []
    if not isinstance(items, list) or not items:
        return jsonify({'success': False, 'error': '请提供至少一个账号'}), 400

    group_id = data.get('group_id')
    remark = (data.get('remark') or '').strip()[:500]

    created: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []

    for raw in items:
        if not isinstance(raw, dict):
            continue
        email_addr = (raw.get('email') or '').strip()
        if not email_addr or '@' not in email_addr:
            skipped.append({'email': email_addr, 'reason': '邮箱无效'})
            continue
        domain = _domain_from_email(email_addr)
        base_url = (raw.get('base_url') or '').strip() or get_internal_eml_baseurl_for_domain(domain) or ''
        if not base_url:
            skipped.append({'email': email_addr, 'reason': f'域名 {domain} 无法解析 baseURL'})
            continue
        api_key = (raw.get('api_key') or '').strip() or get_internal_eml_default_key()

        conn = sqlite3.connect(DATABASE)
        try:
            cur = conn.cursor()
            existing = cur.execute('SELECT id FROM accounts WHERE email = ?', (email_addr,)).fetchone()
            if existing:
                skipped.append({'email': email_addr, 'reason': '已存在'})
                continue
            actual_group_id = group_id
            if actual_group_id is None:
                row = cur.execute(
                    "SELECT id FROM groups WHERE name != '临时邮箱' ORDER BY sort_order, id LIMIT 1"
                ).fetchone()
                actual_group_id = row[0] if row else 1
            encrypted_api_key = encrypt_data(api_key) if api_key else api_key
            cur.execute('''
                INSERT INTO accounts
                (email, password, client_id, refresh_token, group_id, sort_order, remark,
                 status, account_type, provider, imap_host, imap_port, imap_password,
                 forward_enabled, created_at, updated_at)
                VALUES (?, '', '', '', ?, 0, ?, 'active', 'internal_eml', 'internal_eml',
                        ?, 0, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (email_addr, actual_group_id, remark, base_url, encrypted_api_key))
            created.append({'id': cur.lastrowid, 'email': email_addr, 'base_url': base_url})
            conn.commit()
        except Exception as exc:
            skipped.append({'email': email_addr, 'reason': str(exc)})
        finally:
            conn.close()

    return jsonify({
        'success': True,
        'created_count': len(created),
        'skipped_count': len(skipped),
        'created': created,
        'skipped': skipped,
    })


@app.route('/api/internal-eml/<int:account_id>/refresh', methods=['POST'])
@login_required
def api_internal_eml_refresh(account_id):
    account = _fetch_internal_eml_account(account_id)
    if not account:
        return jsonify({'success': False, 'error': '账号不存在或不是 internal_eml 类型'}), 404
    fetched, deleted, error = fetch_and_store_internal_eml(account)
    return jsonify({
        'success': error is None,
        'fetched': fetched,
        'deleted': deleted,
        'error': error,
    })


@app.route('/api/internal-eml/<int:account_id>/messages', methods=['GET'])
@login_required
def api_internal_eml_list(account_id):
    account = _fetch_internal_eml_account(account_id)
    if not account:
        return jsonify({'success': False, 'error': '账号不存在或不是 internal_eml 类型'}), 404

    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'page/per_page 参数无效'}), 400

    keyword = (request.args.get('keyword', '') or '').strip()

    conn = get_db()
    where_sql = 'WHERE account_id = ?'
    params: List[Any] = [account_id]
    if keyword:
        where_sql += ' AND (subject LIKE ? OR from_addr LIKE ? OR body_text LIKE ?)'
        like = f'%{keyword}%'
        params.extend([like, like, like])

    total_row = conn.execute(
        f'SELECT COUNT(*) AS cnt FROM internal_eml_messages {where_sql}', params
    ).fetchone()
    total = total_row['cnt'] if total_row else 0

    rows = conn.execute(
        f'''SELECT id, subject, from_addr, to_addr, has_attachment,
                   received_at, fetched_at, is_read
            FROM internal_eml_messages {where_sql}
            ORDER BY COALESCE(received_at, fetched_at) DESC
            LIMIT ? OFFSET ?''',
        params + [per_page, (page - 1) * per_page]
    ).fetchall()

    return jsonify({
        'success': True,
        'total': total,
        'page': page,
        'per_page': per_page,
        'messages': [dict(r) for r in rows],
    })


@app.route('/api/internal-eml/<int:account_id>/messages/<int:msg_id>', methods=['GET'])
@login_required
def api_internal_eml_detail(account_id, msg_id):
    account = _fetch_internal_eml_account(account_id)
    if not account:
        return jsonify({'success': False, 'error': '账号不存在或不是 internal_eml 类型'}), 404

    conn = get_db()
    row = conn.execute(
        '''SELECT id, account_id, subject, from_addr, to_addr,
                  body_text, body_html, has_attachment,
                  received_at, fetched_at, is_read
           FROM internal_eml_messages WHERE id = ? AND account_id = ?''',
        (msg_id, account_id)
    ).fetchone()
    if not row:
        return jsonify({'success': False, 'error': '邮件不存在'}), 404

    msg = dict(row)

    if not msg.get('is_read'):
        conn.execute('UPDATE internal_eml_messages SET is_read = 1 WHERE id = ?', (msg_id,))
        conn.commit()
        msg['is_read'] = 1

    attachments: List[Dict[str, Any]] = []
    if msg.get('has_attachment'):
        raw_row = conn.execute(
            'SELECT raw_eml FROM internal_eml_messages WHERE id = ?', (msg_id,)
        ).fetchone()
        if raw_row and raw_row['raw_eml']:
            try:
                attachments = parse_eml_bytes(raw_row['raw_eml']).get('attachments', [])
            except Exception:
                attachments = []
    msg['attachments'] = attachments

    return jsonify({'success': True, 'message': msg})


@app.route('/api/internal-eml/<int:account_id>/messages/<int:msg_id>', methods=['DELETE'])
@login_required
def api_internal_eml_delete_local(account_id, msg_id):
    account = _fetch_internal_eml_account(account_id)
    if not account:
        return jsonify({'success': False, 'error': '账号不存在'}), 404
    conn = get_db()
    conn.execute(
        'DELETE FROM internal_eml_messages WHERE id = ? AND account_id = ?',
        (msg_id, account_id)
    )
    conn.commit()
    return jsonify({'success': True})


@app.route('/api/internal-eml/<int:account_id>/messages/<int:msg_id>/attachments/<int:att_idx>',
           methods=['GET'])
@login_required
def api_internal_eml_attachment(account_id, msg_id, att_idx):
    account = _fetch_internal_eml_account(account_id)
    if not account:
        return jsonify({'success': False, 'error': '账号不存在'}), 404

    conn = get_db()
    row = conn.execute(
        'SELECT raw_eml FROM internal_eml_messages WHERE id = ? AND account_id = ?',
        (msg_id, account_id)
    ).fetchone()
    if not row or not row['raw_eml']:
        return jsonify({'success': False, 'error': '邮件原文不存在'}), 404

    msg = BytesParser(policy=policy.default).parsebytes(row['raw_eml'])
    for idx, part in enumerate(msg.iter_attachments()):
        if idx != att_idx:
            continue
        payload = part.get_payload(decode=True) or b''
        filename = part.get_filename() or f'attachment_{att_idx}'
        response = make_response(payload)
        response.headers['Content-Type'] = part.get_content_type() or 'application/octet-stream'
        response.headers['Content-Disposition'] = f'attachment; filename="{quote(filename)}"'
        return response

    return jsonify({'success': False, 'error': '附件不存在'}), 404
