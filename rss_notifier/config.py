from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    rss_feed_url: str
    database_path: str = "./data/rss_seen.sqlite"
    poll_interval_seconds: int = Field(default=300, ge=60)
    notification_dry_run: bool = True

    @model_validator(mode="after")
    def _telegram_if_not_dry_run(self) -> "Settings":
        if not self.notification_dry_run:
            if not self.telegram_bot_token.strip() or not self.telegram_chat_id.strip():
                raise ValueError("Нужны TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID, если NOTIFICATION_DRY_RUN=false")
        return self


def load_settings() -> Settings:
    return Settings()
