"""Bounded local diagnostics for server errors and browser artwork events."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import threading
import time
import secrets
from collections import OrderedDict
from urllib.parse import urlsplit, urlunsplit
from .runtime_redaction import redact_personal


LOG_LOCK = threading.Lock()
LOG_BYTES = 5 * 1024 * 1024
EVENTS = {'card_removed', 'image_load_failed', 'image_load_recovered', 'video_retry', 'video_failed'}
COMMUNITY_OPERATIONS={'status','gallery','detail','verify','recommend','withdraw','report',
    'thumbnail','history_thumbnail','auth_status','challenge','exchange','reconnect','enrichment'}
_COMMUNITY_LOCK=threading.Lock()
_COMMUNITY_RECENT=OrderedDict()

def community_failure(root, operation, error):
    """Allowlisted facts only. Never stringify an exception, its class or causes."""
    operation=operation if operation in COMMUNITY_OPERATIONS else 'other'
    category=('timeout' if isinstance(error,TimeoutError) else
              'transport' if isinstance(error,OSError) else
              'invalid_response' if isinstance(error,(ValueError,TypeError)) else 'unexpected')
    key=(str(Path(root).resolve()),operation,category);now=time.monotonic()
    with _COMMUNITY_LOCK:
        prior=_COMMUNITY_RECENT.get(key)
        if prior and now-prior[0]<60:return prior[1]
        correlation=secrets.token_hex(8)
        _COMMUNITY_RECENT[key]=(now,correlation);_COMMUNITY_RECENT.move_to_end(key)
        while len(_COMMUNITY_RECENT)>64:_COMMUNITY_RECENT.popitem(last=False)
    stamp=datetime.now(timezone.utc).isoformat()
    append_log(Path(root),event=operation,category=category)
    return correlation


def redact_sensitive(message: str) -> str:
    """Best-effort defense against credentials echoed by upstream error pages."""
    message = redact_personal(message)
    message = re.sub(r'(?i)\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+', r'\1 [redacted]', message)
    keys = r'access[_-]?token|refresh[_-]?token|client[_-]?secret|authorization|api[_-]?key|password'
    message = re.sub(r'''(?i)(\b(?:''' + keys + r''')\b["']?\s*[:=]\s*)(["'])(?:\\.|(?!\2)[^\r\n])*\2''',
                     r'\1\2[redacted]\2', message)
    message = re.sub(r'''(?i)(\b(?:''' + keys + r''')\b["']?\s*[:=]\s*)(?!["'])([^\s,}\]"']+)''',
                     r'\1[redacted]', message)
    message = re.sub(r'(?i)(https?://)[^/\s:@]+:[^/@\s]+@', r'\1[redacted]@', message)
    return re.sub(r'''(?i)([?&](?:token|access_token|refresh_token|api_key|code)=)[^&#\s"']+''',
                  r'\1[redacted]', message)


def append_log(root: Path, message: str = '', *, event='local_error', category='unexpected') -> None:
    # Never persist caller-provided text: it may include response content or account data.
    allowed = EVENTS | COMMUNITY_OPERATIONS | {'local_error'}
    event = event if event in allowed else 'local_error'
    category = category if category in {'timeout', 'transport', 'invalid_response', 'unexpected', 'browser'} else 'unexpected'
    message = json.dumps({'timestamp': datetime.now(timezone.utc).isoformat(),
                          'event': event, 'category': category}) + '\n'
    try:
        with LOG_LOCK:
            root.mkdir(parents=True, exist_ok=True)
            path = root / 'error.log'
            if path.exists() and path.stat().st_size + len(message.encode('utf-8')) > LOG_BYTES:
                path.replace(root / 'error.log.1')
            with path.open('a', encoding='utf-8') as output:
                output.write(message)
    except OSError:
        pass


def log_browser_events(root: Path, events: object) -> None:
    if not isinstance(events, list) or not 1 <= len(events) <= 10:
        raise ValueError('Provide 1 to 10 diagnostic events')
    for event in events:
        if not isinstance(event, dict) or event.get('event') not in EVENTS:
            raise ValueError('Unknown diagnostic event')
    for event in events:
        append_log(root, event=event['event'], category='browser')
