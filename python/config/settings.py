"""AIOps 多 Agent 系统全局配置"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Multi-Agent AIOps"
    debug: bool = False

    # 双模开关：True 时使用真实 Kafka / Neo4j，False 时用内存版（默认）
    use_kafka: bool = False
    use_neo4j: bool = False

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_group_id: str = "aiops-agents"
    kafka_topics_alerts: str = "aiops.alerts"
    kafka_topics_events: str = "aiops.events"
    kafka_topics_commands: str = "aiops.commands"
    kafka_topics_audit: str = "aiops.audit"
    kafka_topics_reports: str = "aiops.reports"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "aiops_password"

    # LLM（OpenAI 兼容接口，默认 DeepSeek）
    openai_api_key: Optional[str] = None
    openai_model: str = "deepseek-chat"
    openai_base_url: str = "https://api.deepseek.com"
    llm_timeout_seconds: int = 30

    # Prometheus
    prometheus_url: str = "http://localhost:9090"

    # Agent 配置
    monitor_check_interval: int = 30
    rca_max_depth: int = 5
    heal_dry_run: bool = True
    heal_max_retries: int = 3
    change_auto_approve_threshold: float = 0.9

    # 安全护栏
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    rate_limit_per_minute: int = 30
    blast_radius_max_percent: float = 0.2

    model_config = {"env_prefix": "AIOPS_", "env_file": ".env"}


settings = Settings()
