from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    PUSHOVER_TOKEN: str
    PUSHOVER_USER: str
    
    class Config:
        env_file = ".env"

settings = Settings()