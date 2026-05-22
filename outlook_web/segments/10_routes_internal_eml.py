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
                 timeout: int = 30):
        self.base_url = (base_url or '').rstrip('/')
        self.private_key = private_key or ''
        self.proxies = proxies
        self.timeout = timeout

    def _sign(self, suffix: str) -> Tuple[str, str]:
        ts = str(int(time.time()))
        sig = hashlib.md5((ts + self.private_key + suffix).encode('utf-8')).hexdigest()
        return ts, sig

    def _is_empty(self, body: bytes) -> bool:
        return body == b'EMPTY' or body[:5] == b'EMPTY'

    def get_email(self, email_addr: str) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
        """按收件人拉指定邮件。返回 (content, filename, error)。
        无邮件时 content/filename 都为 None 且 error 为 None。
        """
        ts, sig = self._sign(email_addr)
        params = {'timestamp': ts, 'signature': sig, 'email': email_addr}
        try:
            r = requests.get(f'{self.base_url}/get', params=params,
                             proxies=self.proxies, timeout=self.timeout, verify=False)
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
                             proxies=self.proxies, timeout=self.timeout, verify=False)
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
                             proxies=self.proxies, timeout=self.timeout, verify=False)
        except Exception as exc:
            return False, f'request error: {exc}'
        if r.status_code == 200:
            return True, None
        return False, f'HTTP {r.status_code}: {r.text[:200]}'


def _extract_filename(content_disposition: str) -> str:
    if not content_disposition:
        return ''
    idx = content_disposition.find('filename=')
    if idx < 0:
        return ''
    name = content_disposition[idx + len('filename='):].strip()
    if name.startswith('"'):
        end = name.find('"', 1)
        return name[1:end] if end > 0 else name[1:]
    end = name.find(';')
    if end > 0:
        name = name[:end]
    return name.strip()


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

    private_key = (account.get('imap_password') or '').strip() or get_internal_eml_default_key()

    proxies: Optional[Dict[str, str]] = None
    group_id = account.get('group_id')
    if group_id:
        try:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            grow = conn.execute('SELECT proxy_url FROM groups WHERE id = ?', (group_id,)).fetchone()
            conn.close()
            if grow:
                purl = (grow['proxy_url'] or '').strip()
                if purl:
                    proxies = {'http': purl, 'https': purl}
        except Exception:
            pass

    return InternalEmlClient(base_url, private_key, proxies=proxies)


def _fetch_internal_eml_account(account_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db()
    row = conn.execute(
        'SELECT * FROM accounts WHERE id = ? AND account_type = ?',
        (account_id, 'internal_eml')
    ).fetchone()
    return dict(row) if row else None


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
                    error = f'服务端删除失败 {filename}: {derr}'
                    break
    finally:
        conn.close()

    return fetched, deleted, error


# ==================== HTTP 路由 ====================

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
        'default_key_present': bool(get_internal_eml_default_key()),
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
