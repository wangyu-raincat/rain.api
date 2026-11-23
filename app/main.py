from fastapi import FastAPI

from .api import auth, logs, stats, users
from .core.config import settings
from .core.database import Base, engine
from .models import log_event as _log_event  # noqa: F401  确保建表时模型已注册
from .models import user as _user  # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="1.0.0")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
