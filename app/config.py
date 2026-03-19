from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Customer Support Platform"
    debug: bool = True
    secret_key: str = "change-this-in-production"
    database_url: str = "sqlite:///./support.db"
    groq_api_key: str = ""
    telegram_token: str = ""
    gemini_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    openrouter_api_key: str = ""
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()