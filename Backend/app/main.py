from fastapi import FastAPI, Request, Response
import time
from loguru import logger
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict
from dotenv import load_dotenv
import os

from motor.motor_asyncio import AsyncIOMotorClient 
from pymongo.errors import ConnectionFailure, OperationFailure

from Backend.app.routers import annotation_router 
from Backend.app.routers import chunk_router


# Load environment 
load_dotenv() 

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Lifespan Startup 
    logger.info("Application starting...")
    MONGO_URI = os.getenv("MONGO_URI")
    
    if not MONGO_URI:
        logger.error("MONGO_URI environment variable not set!")
        raise ValueError("MONGO_URI environment variable must be set.")
    
    # Initialize MongoDB client (AsyncIOMotorClient)
    try:
        app.state.mongo_client = AsyncIOMotorClient(MONGO_URI)
        
        # Store the database object globally
        app.state.db = app.state.mongo_client.get_database("chunkDB") 

        # Ping the database to ensure connection is live
        await app.state.db.command('ping')
        logger.info("MongoDB client initialized and connection established successfully.")
        
    except ConnectionFailure as e:
        logger.error(f"FATAL: MongoDB connection failed during startup: {e}")
        
        # Stop application startup if DB is critical
        raise RuntimeError("MongoDB connection is required but failed.")
        
    yield # Application is ready to receive requests

    # Lifespan Shutdown
    logger.info("Application shutting down...")

    # Close the MongoDB client connection without disrupting the other 
    if hasattr(app.state, 'mongo_client') and app.state.mongo_client:
        app.state.mongo_client.close()
        logger.info("MongoDB client connection closed.")

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    start_time = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start_time) * 1000)
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms} ms)"
    )
    return response

app.include_router(annotation_router.router, prefix="/api/v1")
app.include_router(chunk_router.router)


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}
