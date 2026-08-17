from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_host: str = "http://127.0.0.1:11434"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
