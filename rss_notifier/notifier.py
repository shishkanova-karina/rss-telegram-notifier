from __future__ import annotations

import httpx

from rss_notifier.models import Post


class Notifier:
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        *,
        dry_run: bool = True,
    ) -> None:
        self._chat_id = chat_id.strip()
        self._dry_run = dry_run
        self._url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    @property
    def dry_run(self) -> bool:
        return self._dry_run

    def send_notification(self, post: Post) -> None:
        text = f"<b>{_escape_html(post.title)}</b>\n{post.link}"
        if self._dry_run:
            print(f"[dry-run] {post.title}\n{post.link}")
            return

        chat: str | int = self._chat_id
        if self._chat_id.lstrip("-").isdigit():
            chat = int(self._chat_id)

        payload = {
            "chat_id": chat,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(self._url, json=payload)

        if resp.is_success:
            return
        try:
            detail = resp.json().get("description", resp.text)
        except ValueError:
            detail = resp.text or resp.reason_phrase
        extra = ""
        if resp.status_code == 400 and "chat not found" in str(detail).lower():
            extra = (
                " Добавьте бота в чат, отправьте там сообщение, "
                "затем откройте getUpdates в API и скопируйте chat.id в TELEGRAM_CHAT_ID."
            )
        raise RuntimeError(f"Telegram: {resp.status_code} {detail}.{extra}") from None


def _escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
