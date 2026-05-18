from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "VSCC_", "env_file": ".env", "extra": "ignore"}

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    db_dialect: str = "postgresql"
    test_framework: str = "pytest"

    max_iterations: int = 10
    max_session_usage_pct: int = 80

    output_dir: str = "./output"
    logs_dir: str = ""


settings = Settings()
