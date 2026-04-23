from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = Field(default="G&G Homes API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    database_url: str = Field(alias="DATABASE_URL")
    secret_key: str = Field(alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=10080, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    cors_origins_raw: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    flutterwave_public_key: str = Field(default="", alias="FLUTTERWAVE_PUBLIC_KEY")
    flutterwave_secret_key: str = Field(default="", alias="FLUTTERWAVE_SECRET_KEY")
    flutterwave_encryption_key: str = Field(default="", alias="FLUTTERWAVE_ENCRYPTION_KEY")
    flutterwave_webhook_secret: str = Field(default="", alias="FLUTTERWAVE_WEBHOOK_SECRET")
    cloudinary_cloud_name: str = Field(default="", alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str = Field(default="", alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(default="", alias="CLOUDINARY_API_SECRET")
    resend_api_key: str = Field(default="", alias="RESEND_API_KEY")
    email_from: str = Field(default="noreply@gandghomesltd.org", alias="EMAIL_FROM")
    cron_secret: str = Field(default="", alias="CRON_SECRET")
    admin_email: str = Field(default="admin@gandghomesltd.org", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="ChangeMe123!", alias="ADMIN_PASSWORD")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")
    google_maps_api_key: str = Field(default="", alias="GOOGLE_MAPS_API_KEY")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
