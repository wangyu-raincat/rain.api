from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.deps import get_current_user, get_db
from ..models.user import User
from ..schemas.stats import LevelCount, StatsSummary, TrendPoint
from ..services import log_events as log_service

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary", response_model=StatsSummary)
def summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total, rows = log_service.stats_summary(db, current_user.id)
    return StatsSummary(
        total=total,
        by_level=[LevelCount(level=level, count=count) for level, count in rows],
    )


@router.get("/trend", response_model=list[TrendPoint])
def trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return log_service.stats_trend(db, current_user.id)
