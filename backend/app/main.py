from fastapi import FastAPI
from app.api.v1 import router as v1_router

app = FastAPI(title="AI video intelligence platform")
app.include_router(v1_router)


@app.get("/health")
def health():
    return {"status": "ok"}
