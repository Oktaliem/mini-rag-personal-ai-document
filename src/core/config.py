"""
Configuration management for Mini RAG application.
Uses Pydantic Settings for type-safe configuration with environment variable support.
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic.functional_validators import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = Field(default="Mini RAG API", validation_alias="APP_NAME")
    app_version: str = Field(default="2.0.0", validation_alias="APP_VERSION")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", validation_alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_minutes: int = Field(default=10080, validation_alias="REFRESH_TOKEN_EXPIRE_MINUTES")  # 7 days
    algorithm: str = Field(default="HS256", validation_alias="ALGORITHM")
    
    # CORS
    cors_origins: List[str] = Field(default=["*"], validation_alias="CORS_ORIGINS")
    cors_credentials: bool = Field(default=True, validation_alias="CORS_CREDENTIALS")
    cors_methods: List[str] = Field(default=["*"], validation_alias="CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], validation_alias="CORS_HEADERS")
    
    # Ollama
    ollama_url: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_URL")
    generation_model: str = Field(default="llama3.1:8b", validation_alias="GEN_MODEL")
    gen_model: str = Field(default="llama3.1:8b", validation_alias="GEN_MODEL")  # Alias for backward compatibility
    embedding_model: str = Field(default="nomic-embed-text", validation_alias="EMB_MODEL")
    emb_model: str = Field(default="nomic-embed-text", validation_alias="EMB_MODEL")  # Alias for backward compatibility
    
    # Qdrant
    qdrant_url: str = Field(default="http://localhost:6333", validation_alias="QDRANT_URL")
    qdrant_collection: str = Field(default="rag_chunks", validation_alias="QDRANT_COLLECTION")
    
    # Document Processing
    docs_dir: str = Field(default="docs", validation_alias="DOCS_DIR")
    chunk_size: int = Field(default=800, validation_alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, validation_alias="CHUNK_OVERLAP")
    top_k: int = Field(default=6, validation_alias="TOP_K")
    
    # File Upload
    max_file_size: int = Field(default=10 * 1024 * 1024, validation_alias="MAX_FILE_SIZE")  # 10MB
    allowed_extensions: set = Field(default={".pdf", ".md", ".txt"}, validation_alias="ALLOWED_EXTENSIONS")
    
    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", validation_alias="LOG_FORMAT")
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str] | object:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("cors_methods", mode="before")
    @classmethod
    def parse_cors_methods(cls, v: object) -> list[str] | object:
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v
    
    @field_validator("cors_headers", mode="before")
    @classmethod
    def parse_cors_headers(cls, v: object) -> list[str] | object:
        if isinstance(v, str):
            return [header.strip() for header in v.split(",")]
        return v
    
    @field_validator("allowed_extensions", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, v: object) -> set[str] | object:
        if isinstance(v, str):
            return {ext.strip() for ext in v.split(",")}
        return v
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency to get settings instance."""
    return settings
