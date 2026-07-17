from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
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
    document_access_token_secret: str = ""
    document_access_default_ttl_seconds: int = 300
    document_access_max_ttl_seconds: int = 900
    document_access_default_max_uses: int = 1
    document_access_max_uses: int = 5
    document_storage_production_strict: bool = False
    document_storage_allow_local_in_production: bool = False
    minio_auto_create_bucket: bool = True
    minio_server_side_encryption: bool = False
    document_storage_retention_days: int = 0
    document_storage_backup_strategy: str = ""
    document_storage_recovery_tested_at: str = ""
    ollama_base_url: str = "http://localhost:11434"
    default_local_model: str = "qwen2.5:7b"

    # Remote LLM providers (switchable based on active subscription)
    llm_provider: str = ""  # "deepseek" or "moonshot"; empty = deterministic template only
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"
    moonshot_api_key: str = ""
    moonshot_model: str = "kimi-k1-5"
    moonshot_base_url: str = "https://api.moonshot.cn/v1"
    llm_temperature: float = 0.2
    llm_timeout_seconds: int = 60
    llm_fallback_to_template: bool = True

    jwt_secret: str = "change-this-in-production"
    auth_enabled: bool = True
    auth_admin_username: str = "admin"
    auth_admin_password: str = "admin"
    auth_session_cookie: str = "gmai_session"
    auth_allow_header_role: bool = True
    truth_engine_strict_mode: bool = True
    source_monitor_timeout_seconds: int = 30
    source_monitor_max_bytes: int = 5_000_000
    source_monitor_allow_http: bool = False
    regulatory_model_classification_enabled: bool = False
    coverage_tranche_assistant_enabled: bool = False
    coverage_tranche_assistant_max_items: int = 25

    def parsed_cors_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
