from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.asyncexitstack import AsyncExitStackMiddleware
from starlette.middleware import Middleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.exceptions import ExceptionMiddleware

from app.api.router import api_router
from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.db.session import ensure_sqlite_schema

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    for path in [settings.raw_storage_path, settings.processed_storage_path, Path("logs")]:
        path.mkdir(parents=True, exist_ok=True)
    ensure_sqlite_schema()
    yield


class CompatFastAPI(FastAPI):
    def build_middleware_stack(self):
        debug = self.debug
        error_handler = None
        exception_handlers = {}

        for key, value in self.exception_handlers.items():
            if key in (500, Exception):
                error_handler = value
            else:
                exception_handlers[key] = value

        middleware = (
            [Middleware(ServerErrorMiddleware, handler=error_handler, debug=debug)]
            + self.user_middleware
            + [
                Middleware(ExceptionMiddleware, handlers=exception_handlers, debug=debug),
                Middleware(AsyncExitStackMiddleware),
            ]
        )

        app = self.router
        for item in reversed(middleware):
            if isinstance(item, Middleware):
                app = item.cls(app, *item.args, **item.kwargs)
            else:
                cls, options = item
                app = cls(app=app, **options)
        return app


app = CompatFastAPI(
    title=settings.project_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.include_router(api_router)
