from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./gmai.db"
    database_auto_create_tables: Optional[bool] = None
    database_echo: bool = False
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "global_mobility_memory"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_documents: str = "gmai-documents"
    minio_secure: bool = False
    document_storage_backend: str = "local"
    document_local_storage_dir: str = "storage/documents"
    document_upload_max_mb: int = 25
    ollama_base_url: str = "http://localhost:11434"
    default_local_model: str = "qwen2.5:7b"
    jwt_secret: str = "change-this-in-production"
    auth_enabled: bool = True
    auth_admin_username: str = "admin"
    auth_admin_password: str = "admin"
    auth_session_cookie: str = "gmai_session"
    auth_allow_header_role: bool = True
    truth_engine_strict_mode: bool = True


settings = Settings()
