from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Banco de dados (PostgreSQL)
    database_url: str = "postgresql+psycopg://gmc:gmc@localhost:5432/gmc"

    # Aplicação
    port: int = 8000
    secret_key: str
    token_minutes: int = 720
    cors_origins: str = "*"
    static_dir: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
