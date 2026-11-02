import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    database_uri: str
    openai_api_key: str
    openai_model:str
    ai_mode:str
    cookie_secure: bool
    ai_max_request_per_hour: int
    jwt_secret: str

def get_settings() -> Settings:
    return Settings(
        database_uri=os.getenv("DATABASE_URI", ''),
        openai_api_key=os.getenv("OPENAI_API_KEY", ''),
        openai_model=os.getenv("OPENAI_MODEL", ''),
        ai_mode=os.getenv("AI_MODE", ''),
        cookie_secure=os.getenv("COOKIE_SECURE", "").lower() == "true",
        ai_max_request_per_hour=int(os.getenv("AI_MAX_REQUEST_PER_HOUR", '0')),
        jwt_secret=os.getenv("JWT_SECRET", ''),
    )