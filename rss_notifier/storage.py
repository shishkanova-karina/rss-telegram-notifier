from __future__ import annotations

import sqlite3
from pathlib import Path

from rss_notifier.models import Post


class Storage:
    def __init__(self, database_path: str) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_posts (
                content_hash TEXT PRIMARY KEY,
                link TEXT NOT NULL,
                title TEXT NOT NULL,
                notified_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
        return conn

    def is_known(self, content_hash: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM seen_posts WHERE content_hash = ? LIMIT 1",
                (content_hash,),
            ).fetchone()
        return row is not None

    def save_post(self, post: Post) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO seen_posts (content_hash, link, title) VALUES (?, ?, ?)",
                (post.content_hash, post.link, post.title),
            )
            conn.commit()
