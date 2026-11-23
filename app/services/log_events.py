"""日志事件业务逻辑层：CRUD、筛选与统计聚合。"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.log_event import LogEvent
from ..schemas.log_event import LogEventCreate


def create_log(db: Session, owner_id: int, data: LogEventCreate) -> LogEvent:
    log = LogEvent(
        level=data.level.value, source=data.source, message=data.message,
        owner_id=owner_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_logs(
    db: Session,
    owner_id: int,
    page: int = 1,
    size: int = 20,
    level: str | None = None,
    source: str | None = None,
) -> tuple[int, list[LogEvent]]:
    query = db.query(LogEvent).filter(LogEvent.owner_id == owner_id)
    if level:
        query = query.filter(LogEvent.level == level)
    if source:
        query = query.filter(LogEvent.source == source)
    total = query.count()
    items = (
        query.order_by(LogEvent.created_at.desc(), LogEvent.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return total, items


def get_log(db: Session, owner_id: int, log_id: int) -> LogEvent | None:
    return (
        db.query(LogEvent)
        .filter(LogEvent.id == log_id, LogEvent.owner_id == owner_id)
        .first()
    )


def delete_log(db: Session, log: LogEvent) -> None:
    db.delete(log)
    db.commit()


def stats_summary(db: Session, owner_id: int) -> tuple[int, list[tuple[str, int]]]:
    rows = (
        db.query(LogEvent.level, func.count(LogEvent.id))
        .filter(LogEvent.owner_id == owner_id)
        .group_by(LogEvent.level)
        .all()
    )
    return sum(c for _, c in rows), rows


def stats_trend(db: Session, owner_id: int) -> list[dict]:
    """最近 24 小时按小时聚合（含当前整点，共 24 个桶）。"""
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(hours=23)
    logs = (
        db.query(LogEvent.created_at)
        .filter(LogEvent.owner_id == owner_id, LogEvent.created_at >= start)
        .all()
    )
    buckets: dict[datetime, int] = {start + timedelta(hours=i): 0 for i in range(24)}
    for (created_at,) in logs:
        if created_at.tzinfo is None:  # SQLite 读回为 naive 时间，按 UTC 处理
            created_at = created_at.replace(tzinfo=timezone.utc)
        hour = created_at.replace(minute=0, second=0, microsecond=0)
        if hour in buckets:
            buckets[hour] += 1
    return [
        {"hour": h.isoformat(), "count": buckets[h]} for h in sorted(buckets)
    ]
