import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .api.v1.router import api_router
from .events.consumers import start_consumers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start RabbitMQ consumer loop in background
    consumer_task = asyncio.create_task(start_consumers())
    yield
    # On shutdown, cancel the background task
    consumer_task.cancel()

app = FastAPI(title="notification-service", version="1.0.0", lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notification-service"}

app.include_router(api_router, prefix="/api/v1")
