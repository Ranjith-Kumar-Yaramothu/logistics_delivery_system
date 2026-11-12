from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "Ranjith@436"
    DB_NAME: str = "logistics_db"
    RANDOM_SEED: int = 20261022
    DATA_MODE: str = "starter"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
