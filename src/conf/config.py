from pydantic_settings import BaseSettings  # Оновлений імпорт
from pathlib import Path

class Settings(BaseSettings):
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str

    JWT_SECRET: str  # Секретний ключ для токенів
    JWT_ALGORITHM: str  # Алгоритм шифрування токенів
    JWT_EXPIRATION_SECONDS: int  # Час дії токена (1 година)

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    TEMPLATE_FOLDER: Path = Path(__file__).parent.parent/ 'services' / 'templates'

    CLD_NAME: str
    CLD_API_KEY: int
    CLD_API_SECRET: str

    @property
    def database_url(self) -> str:
        """Формує URL для підключення до PostgreSQL."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        extra = "allow"
        env_file = ".env"  # Вказуємо, що змінні середовища беруться з .env файлу

settings = Settings()