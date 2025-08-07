from dotenv import load_dotenv, find_dotenv
import os
from functools import lru_cache

# Load default first
load_dotenv(dotenv_path=".env.local", override=False)

# Then override with .env if available
load_dotenv(dotenv_path=find_dotenv(".env"), override=True)


class Settings:
    POSTGRES_URI: str | None = os.getenv("POSTGRES_URI")

    def __init__(self):
        if not self.POSTGRES_URI:
            raise ValueError("POSTGRES_URI is missing in the environment variables.")


@lru_cache()
def get_settings():
    return Settings()