import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Central configuration class for environment variables and model settings.
    """
    # DIAL API / Azure OpenAI settings from .env
    DIAL_API_KEY = os.getenv("DIAL_API_KEY")
    DIAL_API_VERSION = os.getenv("DIAL_API_VERSION")
    DIAL_API_ENDPOINT = os.getenv("DIAL_API_ENDPOINT")

    # JWT settings
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    ALGORITHM: str = os.getenv("JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # PostgreSQL connection settings
    POSTGRES_DB = os.getenv("POSTGRES_DB", "resume_screener_db")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mysecretpassword")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

    # MongoDB settings
    MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
    MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
    MONGO_INITDB_ROOT_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
    MONGO_INITDB_ROOT_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "password")
    MONGO_DB = os.getenv("MONGO_DB", "resume_screener_db")

    @classmethod
    def get_postgres_url(cls) -> str:
        """Construct PostgreSQL connection URL"""
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"