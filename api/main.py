import logging
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api.routes import admin, appointments, auth, cron, notifications, payments, properties, saved, uploads, users
from core.config import settings
from db.session import Base, engine


logger = logging.getLogger("gghomes.api")


def create_application() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    Base.metadata.create_all(bind=engine)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started_at = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - started_at) * 1000
            logger.exception("Unhandled backend error", extra={
                "method": request.method,
                "path": request.url.path,
                "query": request.url.query,
                "duration_ms": round(duration_ms, 2),
            })
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error. Check backend logs for request context."},
            )

        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "Request handled",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": request.url.query,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        return response

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(properties.router, prefix="/api/properties", tags=["properties"])
    app.include_router(appointments.router, prefix="/api/appointments", tags=["appointments"])
    app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
    app.include_router(uploads.router, prefix="/api/upload", tags=["upload"])
    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
    app.include_router(saved.router, prefix="/api/saved", tags=["saved"])
    app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
    app.include_router(cron.router, prefix="/api/cron", tags=["cron"])

    @app.get("/api/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_application()
