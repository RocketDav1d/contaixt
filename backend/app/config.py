from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"

    # Postgres
    database_url: str = "postgresql+asyncpg://contaixt:contaixt@postgres:5432/contaixt"
    database_url_sync: str = "postgresql+psycopg://contaixt:contaixt@postgres:5432/contaixt"

    # Neo4j
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "contaixt"
    neo4j_database: str = "neo4j"

    # OpenAI
    openai_api_key: str = ""

    # Nango
    nango_secret_key: str = ""
    nango_webhook_secret: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
