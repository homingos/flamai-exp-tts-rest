# /app.py

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import os
from dotenv import load_dotenv

# --- FINAL, BULLETPROOF FIX ---
# Load the .env file at the earliest possible moment.
load_dotenv()
# ------------------------------

from src.api.routes import router as api_router
from src.core.server_manager import create_server_manager, ServerManager
from src.core.process_manager import create_process_manager, ProcessManager
from src.utils.resources.logger import logger
from src.utils.config.settings import settings

# Global instances
server_manager: ServerManager = None
process_manager: ProcessManager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global server_manager, process_manager
    logger.info(f"Starting {settings.get('app.name', 'TTS API Service')}")
    try:
        process_manager = create_process_manager()
        app.state.process_manager = process_manager
        server_manager = create_server_manager()
        app.state.server_manager = server_manager
        await _register_services(server_manager)
        server_manager.setup_signal_handlers()
        if not await server_manager.initialize():
            raise RuntimeError("Server manager initialization failed.")
        logger.info(f"{settings.get('app.name')} started successfully. All services are ready.")
    except Exception as e:
        logger.error(f"Error during application startup: {e}", exc_info=True)
        raise
    yield
    logger.info(f"Shutting down {settings.get('app.name')}")
    try:
        if server_manager:
            await server_manager.shutdown()
            logger.info("Server manager shutdown complete.")
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}", exc_info=True)

async def _register_services(manager: ServerManager):
    from src.services.tts_service import MinimaxTtsService
    from src.core.server_manager import ServiceConfig
    
    services_config = settings.get("server_manager.services", {})
    if "minimax_tts" in services_config:
        tts_config_data = services_config["minimax_tts"]
        if tts_config_data.get("enabled", True):
            # --- NEW ROBUST LOGIC ---
            # Directly load credentials from the environment here.
            api_key = os.getenv("MINIMAX_API_KEY")
            group_id = os.getenv("MINIMAX_GROUP_ID")
            
            if not api_key or not group_id:
                msg = "FATAL: MINIMAX_API_KEY or MINIMAX_GROUP_ID not found. Check your .env file."
                logger.error(msg)
                raise RuntimeError(msg)
            
            # Create the config with the guaranteed correct values.
            service_specific_config = {
                "api_key": api_key,
                "group_id": group_id
            }
            # -------------------------

            service_config = ServiceConfig(
                name="minimax_tts",
                config=service_specific_config # Pass the correct config
            )
            tts_service = MinimaxTtsService(service_config)
            manager.register_service(tts_service)
            logger.info("Minimax TTS service registered.")

app = FastAPI(
    title=settings.get("app.name", "TTS API Service"),
    description=settings.get("app.description"),
    version=settings.get("app.version", "1.0.0"),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

if settings.get("cors"):
    app.add_middleware(CORSMiddleware, allow_origins=settings.get("cors.allow_origins", ["*"]), allow_credentials=settings.get("cors.allow_credentials", True), allow_methods=settings.get("cors.allow_methods", ["*"]), allow_headers=settings.get("cors.allow_headers", ["*"]))
app.include_router(api_router)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/status", tags=["Health"])
async def get_status():
    return {"status": "ok", "service": settings.get("app.name")}

if __name__ == "__main__":
    server_config = settings.get_server_config()
    uvicorn.run("app:app", host=server_config.get("host", "0.0.0.0"), port=server_config.get("port", 8000), reload=server_config.get("reload", False), workers=server_config.get("workers", 1))