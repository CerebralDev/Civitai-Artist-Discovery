"""Durable, account-bound barriers for compound comment/collection actions.

Persist intent before contacting Civitai. An uncertain or partial result is never
replayed, including after restart. Reconciliation is an explicit website action.
No credentials, comment text, usernames or resource URLs are stored here.
"""
from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
import threading


class WriteBlocked(RuntimeError):
    pass


class WriteGuard:
    def __init__(self, path: Path | None = None):
        self.path = path
        self.lock = threading.RLock()
        self.memory = {}
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(path)) as db, db:
                db.execute('CREATE TABLE IF NOT EXISTS write_outcomes '
                           '(action_key TEXT PRIMARY KEY, state TEXT NOT NULL)')

    @staticmethod
    def key(account, action, collection, item):
        if type(account) is not int or account <= 0:
            raise PermissionError('Sign in before changing a collection')
        value = f'{account}:{action}:{int(collection)}:{int(item)}'
        return hashlib.sha256(value.encode()).hexdigest()

    def begin(self, key):
        with self.lock:
            if self.path is None:
                if key in self.memory:
                    raise WriteBlocked('This action may already have posted a comment. '
                                       'Review and finish it on Civitai; it will not be posted again here.')
                self.memory[key] = 'pending'
                return
            with closing(sqlite3.connect(self.path)) as db, db:
                try:
                    db.execute('INSERT INTO write_outcomes VALUES (?, ?)', (key, 'pending'))
                except sqlite3.IntegrityError:
                    raise WriteBlocked('This action may already have posted a comment. '
                                       'Review and finish it on Civitai; it will not be posted again here.') from None

    def mark(self, key, state):
        if state not in ('commented', 'done'):
            raise ValueError('Invalid write state')
        with self.lock:
            if self.path is None:
                self.memory[key] = state
            else:
                with closing(sqlite3.connect(self.path)) as db, db:
                    db.execute('UPDATE write_outcomes SET state=? WHERE action_key=?', (state, key))
