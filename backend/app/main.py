import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import health, overview, samples, sensors
from .database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FreshFusion API",
    version="0.1.0",
    description="Backend for multimodal fruit freshness intelligence.",
    lifespan=lifespan,
)

origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(samples.router)
app.include_router(sensors.router)
app.include_router(overview.router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "FreshFusion API",
        "status": "running",
        "docs": "/docs",
    }
