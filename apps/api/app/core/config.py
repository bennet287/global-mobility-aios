from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./gmai.db"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "global_mobility_memory"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_documents: str = "gmai-documents"
    minio_secure: bool = False
    ollama_base_url: str = "http://localhost:11434"
    default_local_model: str = "qwen2.5:7b"
    jwt_secret: str = "change-this-in-production"
    truth_engine_strict_mode: bool = True


settings = Settings()
