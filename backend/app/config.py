from pydantic_settings import BaseSettings

_DEV_ORIGINS = ",".join([
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "http://127.0.0.1:3003",
])


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    chroma_db_path: str = "./chroma_db"
    environment: str = "development"
    # Comma-separated list of allowed CORS origins.
    # In production set this to your Vercel deployment URL, e.g.:
    #   ALLOWED_ORIGINS=https://insuresight.vercel.app
    allowed_origins: str = _DEV_ORIGINS

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
