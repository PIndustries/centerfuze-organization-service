"""
Settings configuration for CenterFuze Organization Service
"""

import os
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Service configuration settings"""
    
    # Service Info
    service_name: str = "centerfuze-organization-service"
    service_version: str = "1.0.0"
    environment: str = "development"
    
    # NATS Configuration
    nats_url: str = "nats://localhost:4222"
    nats_user: Optional[str] = None
    nats_password: Optional[str] = None
    nats_servers: List[str] = []
    
    # MongoDB Configuration
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db_name: str = "centerfuze"
    
    # Redis Configuration (for session/cache)
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "default-admin-insecure-secret-key-please-change"
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour
    
    # Logging
    log_level: str = "INFO"
    
    # Metrics
    enable_metrics: bool = True
    metrics_port: int = 8001
    
    def __init__(self, **values):
        super().__init__(**values)
        # Parse NATS servers from URL if not explicitly set
        if not self.nats_servers and self.nats_url:
            self.nats_servers = [self.nats_url]
            
        # Override from environment
        if os.getenv("NATS_URL"):
            self.nats_url = os.getenv("NATS_URL")
            self.nats_servers = [self.nats_url]
            
        if os.getenv("NATS_USER"):
            self.nats_user = os.getenv("NATS_USER")
            
        if os.getenv("NATS_PASSWORD"):
            self.nats_password = os.getenv("NATS_PASSWORD")
            
        if os.getenv("MONGO_URL"):
            self.mongo_url = os.getenv("MONGO_URL")
            
        if os.getenv("MONGO_DB_NAME"):
            self.mongo_db_name = os.getenv("MONGO_DB_NAME")
            
        if os.getenv("REDIS_URL"):
            self.redis_url = os.getenv("REDIS_URL")
            
        if os.getenv("SECRET_KEY") or os.getenv("ADMIN_SECRET_KEY"):
            self.secret_key = os.getenv("ADMIN_SECRET_KEY", os.getenv("SECRET_KEY"))
            
        if os.getenv("JWT_SECRET_KEY"):
            self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        elif not self.jwt_secret_key:
            self.jwt_secret_key = self.secret_key
            
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()