from datetime import datetime

from pydantic import BaseModel, Field


class Post(BaseModel):
    title: str
    link: str
    published_at: datetime
    content_hash: str = Field(min_length=64, max_length=64)
