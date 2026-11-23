from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ..models.log_event import LogLevel


class LogEventCreate(BaseModel):
    level: LogLevel
    source: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1)


class LogEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    level: LogLevel
    source: str
    message: str
    owner_id: int
    created_at: datetime


class LogEventPage(BaseModel):
    total: int
    page: int
    size: int
    items: list[LogEventOut]
