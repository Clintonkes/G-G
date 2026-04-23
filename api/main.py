from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, appointments, auth, cron, notifications, payments, properties, saved, uploads, users
from app.core.config import settings
from app.db.session import Base, engine


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
