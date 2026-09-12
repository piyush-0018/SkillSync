from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.frontend import FrontendFiles
from app.core.logging import configure_request_logging
from app.core.request_security import RequestSecurityMiddleware


def cors_origins() -> list[str]:
    origins = {settings.frontend_origin}
    if settings.app_env in {"development", "test"}:
        origins.update({"http://localhost:5173", "http://127.0.0.1:5173"})
    return sorted(origins)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/api/docs" if settings.app_env != "production" else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.app_env != "production" else None,
)

app.add_middleware(RequestSecurityMiddleware, allowed_origins=cors_origins())
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Authorization", "Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Pydantic's default errors echo input values, including rejected passwords.
    return JSONResponse(status_code=422, content={
        "detail": [{"loc": error["loc"], "msg": error["msg"], "type": error["type"]} for error in exc.errors()]
    })


request_logger = configure_request_logging(settings.log_level)


@app.middleware("http")
async def protect_api_responses(request: Request, call_next):
    request_id = uuid4().hex
    started = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
    finally:
        # Log route templates, never query strings, credentials, uploads or AI prompts.
        request_logger.info("request_completed", extra={
            "request_id": request_id,
            "method": request.method,
            "route": getattr(request.scope.get("route"), "path", "unmatched"),
            "status": status_code,
            "duration_ms": round((perf_counter() - started) * 1000, 2),
        })
    response.headers["X-Request-ID"] = request_id
    response.headers.setdefault("Cache-Control", "no-store")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    return response

app.include_router(api_router, prefix=settings.api_prefix)

if settings.frontend_dist_dir is not None:
    app.mount("/", FrontendFiles(settings.frontend_dist_dir, settings.api_prefix), name="frontend")
