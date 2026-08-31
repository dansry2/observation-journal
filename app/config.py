from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = {"env_file": ".env"}
    
    DATABASE_URL: str = "sqlite:////app/data/journal.db"
    USERS_DATABASE_URL: str = "sqlite:////app/data/users.db"
    SECRET_KEY: str = "change-me-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""
    SUBPATH: str = ""

settings = Settings()
