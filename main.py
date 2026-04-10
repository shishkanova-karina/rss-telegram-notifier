from __future__ import annotations

import argparse
import sys
import time

from pydantic import ValidationError
from apscheduler.schedulers.blocking import BlockingScheduler

from rss_notifier.config import load_settings
from rss_notifier.notifier import Notifier
from rss_notifier.parser import RSSParser
from rss_notifier.storage import Storage

_TELEGRAM_GAP_SEC = 3.1


def run_tick(parser: RSSParser, storage: Storage, notifier: Notifier) -> None:
    posts = list(parser.fetch_and_parse())
    sent = 0
    for post in posts:
        if storage.is_known(post.content_hash):
            continue
        notifier.send_notification(post)
        storage.save_post(post)
        sent += 1
        if not notifier.dry_run:
            time.sleep(_TELEGRAM_GAP_SEC)
    print(f"Готово: в ленте {len(posts)} записей, отправлено новых: {sent}")


def main() -> int:
    args = argparse.ArgumentParser(description="RSS → Telegram")
    args.add_argument("--once", action="store_true", help="Один проход без планировщика")
    ns = args.parse_args()

    try:
        settings = load_settings()
    except ValidationError as e:
        print(e, file=sys.stderr)
        return 1

    parser = RSSParser(settings.rss_feed_url)
    storage = Storage(settings.database_path)
    notifier = Notifier(
        settings.telegram_bot_token,
        settings.telegram_chat_id,
        dry_run=settings.notification_dry_run,
    )

    if ns.once:
        run_tick(parser, storage, notifier)
        return 0

    sched = BlockingScheduler()
    sched.add_job(
        run_tick,
        "interval",
        seconds=settings.poll_interval_seconds,
        args=[parser, storage, notifier],
        id="rss_poll",
        replace_existing=True,
    )
    print(f"Опрос каждые {settings.poll_interval_seconds} с — {settings.rss_feed_url}")
    sched.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
