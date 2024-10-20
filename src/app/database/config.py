from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Модель данных, загружаемых из .env"""
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_USER: Optional[str] = None
    DB_PASS: Optional[str] = None
    DB_NAME: Optional[str] = None
    SECRET_KEY: Optional[str] = None

    @property
    def DATABASE_URL_psycopg(self):
        """Возвращает URL для подключения к базе данных при помощи psycopg"""
        return (f'postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}')

    model_config = SettingsConfigDict(env_file='.env')


@lru_cache()
def get_settings() -> Settings:
    return Settings()
