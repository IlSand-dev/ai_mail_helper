from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEBUG: bool

    APP_NAME: str
    HOST: str
    PORT: int
    BASE_URL: str

    DOCS_UI_ENABLED: bool
    SWAGGER_PREFIX: str
    REDOC_PREFIX: str

    TG_TOKEN: str

    TOKENS_DIR: str

    GMAIL_MAIN_CREDENTIALS_PATH: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_USER: str
    REDIS_PASSWORD: str

    AI_HOST: str

    model_config = SettingsConfigDict(env_file=".env", extra='allow')

config = Settings()