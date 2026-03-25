import os

# Provide required settings so module imports don't fail during test collection.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("APP_ENV", "test")
