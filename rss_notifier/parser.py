from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Iterable

import feedparser

from rss_notifier.models import Post


def _content_hash(guid: str, title: str, link: str, summary: str) -> str:
    payload = "\n".join((guid, title, link, summary))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _published_at(entry: dict) -> datetime:
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    raw = entry.get("published") or entry.get("updated")
    if raw:
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (TypeError, ValueError):
            pass
    return datetime.now(timezone.utc)


class RSSParser:
    def __init__(self, feed_url: str) -> None:
        self._feed_url = feed_url

    def parse_items(self, feed_body: str | None = None) -> list[Post]:
        parsed = feedparser.parse(feed_body) if feed_body is not None else feedparser.parse(self._feed_url)
        posts: list[Post] = []
        for entry in parsed.entries:
            title = (entry.get("title") or "").strip() or "(без заголовка)"
            link = (entry.get("link") or "").strip()
            if not link:
                continue
            summary = (entry.get("summary") or entry.get("description") or "").strip()
            guid = (entry.get("id") or entry.get("guid") or link).strip()
            posts.append(
                Post(
                    title=title,
                    link=link,
                    published_at=_published_at(entry),
                    content_hash=_content_hash(guid, title, link, summary),
                )
            )
        return posts

    def fetch_and_parse(self) -> Iterable[Post]:
        return self.parse_items()
