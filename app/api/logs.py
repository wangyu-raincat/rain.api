from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core.deps import get_current_user, get_db
from ..models.log_event import LogLevel
from ..models.user import User
from ..schemas.log_event import LogEventCreate, LogEventOut, LogEventPage
from ..services import log_events as log_service

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("", response_model=LogEventOut, status_code=status.HTTP_201_CREATED)
def create_log(
    data: LogEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return log_service.create_log(db, current_user.id, data)


@router.get("", response_model=LogEventPage)
def list_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    level: LogLevel | None = None,
    source: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total, items = log_service.list_logs(
        db,
        current_user.id,
        page=page,
        size=size,
        level=level.value if level else None,
        source=source,
    )
    return LogEventPage(total=total, page=page, size=size, items=items)


@router.get("/{log_id}", response_model=LogEventOut)
def get_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = log_service.get_log(db, current_user.id, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="日志不存在")
    return log


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = log_service.get_log(db, current_user.id, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="日志不存在")
    log_service.delete_log(db, log)
