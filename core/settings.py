from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEBUG: bool

    APP_NAME: str
    HOST: str
    PORT: int

    DOCS_UI_ENABLED: bool
    SWAGGER_PREFIX: str
    REDOC_PREFIX: str

    TG_TOKEN: str

    TOKENS_DIR: str

    GMAIL_MAIN_CREDENTIALS_PATH: str

    model_config = SettingsConfigDict(env_file=".env", extra='allow')

config = Settings()