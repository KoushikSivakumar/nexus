from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware


def frontend_public_dir() -> Path:
    """Resolve ``frontend/public`` from the project layout, never the cwd.

    The canonical layout is::

        <repo root>/
            backend/
                app/
                    main.py          <- this file
            frontend/
                public/
                    index.html
                    styles.css
                    app.js

    In the Docker image / docker-compose the backend is mounted at ``/app``
    (so this file is ``/app/app/main.py``) with the frontend sitting next to it
    at ``/app/frontend/public``. Walking upward from this file covers both
    layouts without depending on the current working directory.
    """
    start = Path(__file__).resolve().parent
    for directory in (start, *start.parents):
        candidate = directory / "frontend" / "public"
        if (candidate / "index.html").is_file():
            return candidate
    raise RuntimeError(
        "frontend/public/ not found; serve NEXUS from a checkout where the "
        "frontend package sits next to the backend package"
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.dependency_overrides[get_settings] = lambda: settings

    app.add_middleware(RequestIdMiddleware, header_name=settings.request_id_header)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    # Frontend serving: the frontend prototype is the visual contract and is
    # mounted read-only below. API routing stays under /api/v1/* untouched.
    frontend_dir = frontend_public_dir()
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(frontend_dir / "index.html")

    return app


app = create_app()
