from pydantic import BaseModel


class LevelCount(BaseModel):
    level: str
    count: int


class StatsSummary(BaseModel):
    total: int
    by_level: list[LevelCount]


class TrendPoint(BaseModel):
    hour: str  # ISO 8601，整点时刻
    count: int
