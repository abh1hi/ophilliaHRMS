from fastapi import FastAPI
from .api.v1.router import api_router

app = FastAPI(title="leave-service", version="1.0.0")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "leave-service"}

app.include_router(api_router, prefix="/api/v1")
