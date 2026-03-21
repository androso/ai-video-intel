from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    APP_ENV: str

    # Google Cloud Storage
    GCS_BUCKET: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # Upload constraints
    MAX_UPLOAD_SIZE_MB: int = 500
    ALLOWED_MIME_TYPES: set[str] = {
        "video/mp4",
        "video/webm",
        "video/ogg",
        "video/mpeg",
        "video/x-msvideo",
        "video/mp2t",
    }

    # AI providers
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    LOCAL_STORAGE_DIR: str = "storage"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property 
    def use_local_storage(self) -> bool:
        return not self.GCS_BUCKET

    model_config = { "env_file": "../.env"}

settings = Settings()