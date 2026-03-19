from fastapi import FastAPI

app = FastAPI(title="AI video intelligence platform")

@app.get("/health")
def health():
    return { "status": "ok" }