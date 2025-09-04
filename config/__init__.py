"""
Configuration management for Triad Terminal.

Centralizes configuration loading and validation for the multi-assistant command center.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration."""
    db_path: str = "~/.triad/history.db"
    dataset_catalog_path: str = "~/.triad/datasets"
    sqlite_echo: bool = False


@dataclass  
class StormConfig:
    """Storm integration configuration."""
    websocket_port: int = 8765
    coordination_timeout: float = 30.0
    redis_url: Optional[str] = None


@dataclass
class MultiAssistantConfig:
    """Multi-assistant configuration."""
    max_active_sessions: int = 10
    session_timeout_minutes: int = 120
    default_assistant_types: List[str] = None

    def __post_init__(self):
        if self.default_assistant_types is None:
            self.default_assistant_types = ["PlannerAgent", "ExecutorAgent", "ChatAgent"]


@dataclass
class APIConfig:
    """API server configuration."""
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    cors_origins: str = "*"


@dataclass
class HistoryConfig:
    """History persistence configuration."""
    retention_days: int = 30
    auto_cleanup_enabled: bool = True
    max_messages_per_room: int = 10000


@dataclass
class DatasetConfig:
    """Dataset catalog configuration."""
    max_dataset_size_mb: int = 100
    supported_formats: List[str] = None
    auto_schema_analysis: bool = True

    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ["csv", "json", "parquet", "txt", "tsv", "excel"]


@dataclass
class LoggingConfig:
    """Logging configuration."""
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "~/.triad/logs/triad.log"


@dataclass
class SecurityConfig:
    """Security configuration."""
    secret_key: str = "your-secret-key-here"
    allowed_hosts: List[str] = None
    enable_api_auth: bool = False

    def __post_init__(self):
        if self.allowed_hosts is None:
            self.allowed_hosts = ["localhost", "127.0.0.1"]


@dataclass
class PerformanceConfig:
    """Performance configuration."""
    worker_threads: int = 4
    connection_pool_size: int = 20
    request_timeout_seconds: int = 30


@dataclass
class FeatureFlags:
    """Feature flags configuration."""
    enable_storm_integration: bool = True
    enable_dataset_catalog: bool = True
    enable_history_persistence: bool = True
    enable_multi_assistant: bool = True
    enable_group_chat: bool = True


@dataclass
class TriadConfig:
    """Main configuration class."""
    database: DatabaseConfig
    storm: StormConfig
    multi_assistant: MultiAssistantConfig
    api: APIConfig
    history: HistoryConfig
    dataset: DatasetConfig
    logging: LoggingConfig
    security: SecurityConfig
    performance: PerformanceConfig
    features: FeatureFlags

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "TriadConfig":
        """Load configuration from environment variables."""
        if env_file:
            load_env_file(env_file)

        return cls(
            database=DatabaseConfig(
                db_path=os.getenv("TRIAD_DB_PATH", "~/.triad/history.db"),
                dataset_catalog_path=os.getenv("DATASET_CATALOG_PATH", "~/.triad/datasets"),
                sqlite_echo=os.getenv("SQLITE_ECHO", "false").lower() == "true"
            ),
            storm=StormConfig(
                websocket_port=int(os.getenv("STORM_WEBSOCKET_PORT", "8765")),
                coordination_timeout=float(os.getenv("STORM_COORDINATION_TIMEOUT", "30.0")),
                redis_url=os.getenv("STORM_REDIS_URL")
            ),
            multi_assistant=MultiAssistantConfig(
                max_active_sessions=int(os.getenv("MAX_ACTIVE_SESSIONS", "10")),
                session_timeout_minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", "120")),
                default_assistant_types=os.getenv("DEFAULT_ASSISTANT_TYPES", "PlannerAgent,ExecutorAgent,ChatAgent").split(",")
            ),
            api=APIConfig(
                host=os.getenv("API_HOST", "127.0.0.1"),
                port=int(os.getenv("API_PORT", "8000")),
                debug=os.getenv("API_DEBUG", "true").lower() == "true",
                cors_origins=os.getenv("CORS_ORIGINS", "*")
            ),
            history=HistoryConfig(
                retention_days=int(os.getenv("HISTORY_RETENTION_DAYS", "30")),
                auto_cleanup_enabled=os.getenv("AUTO_CLEANUP_ENABLED", "true").lower() == "true",
                max_messages_per_room=int(os.getenv("MAX_MESSAGES_PER_ROOM", "10000"))
            ),
            dataset=DatasetConfig(
                max_dataset_size_mb=int(os.getenv("MAX_DATASET_SIZE_MB", "100")),
                supported_formats=os.getenv("SUPPORTED_FORMATS", "csv,json,parquet,txt,tsv,excel").split(","),
                auto_schema_analysis=os.getenv("AUTO_SCHEMA_ANALYSIS", "true").lower() == "true"
            ),
            logging=LoggingConfig(
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                log_format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                log_file=os.getenv("LOG_FILE", "~/.triad/logs/triad.log")
            ),
            security=SecurityConfig(
                secret_key=os.getenv("SECRET_KEY", "your-secret-key-here"),
                allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(","),
                enable_api_auth=os.getenv("ENABLE_API_AUTH", "false").lower() == "true"
            ),
            performance=PerformanceConfig(
                worker_threads=int(os.getenv("WORKER_THREADS", "4")),
                connection_pool_size=int(os.getenv("CONNECTION_POOL_SIZE", "20")),
                request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
            ),
            features=FeatureFlags(
                enable_storm_integration=os.getenv("ENABLE_STORM_INTEGRATION", "true").lower() == "true",
                enable_dataset_catalog=os.getenv("ENABLE_DATASET_CATALOG", "true").lower() == "true",
                enable_history_persistence=os.getenv("ENABLE_HISTORY_PERSISTENCE", "true").lower() == "true",
                enable_multi_assistant=os.getenv("ENABLE_MULTI_ASSISTANT", "true").lower() == "true",
                enable_group_chat=os.getenv("ENABLE_GROUP_CHAT", "true").lower() == "true"
            )
        )


def load_env_file(env_file: str) -> None:
    """Load environment variables from a file."""
    env_path = Path(env_file)
    if not env_path.exists():
        return
    
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


# Global configuration instance
config = TriadConfig.from_env()


def get_config() -> TriadConfig:
    """Get the global configuration instance."""
    return config


def reload_config(env_file: Optional[str] = None) -> TriadConfig:
    """Reload configuration from environment."""
    global config
    config = TriadConfig.from_env(env_file)
    return config