from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.endpoints import router as api_router
from app.api.alerts_endpoints import router as alerts_router
from app.api.dashboard_endpoints import router as dashboard_router
from app.core.config import settings
from app.core.logger import logger
import os

app = FastAPI(title=settings.PROJECT_NAME)
logger.info(f"Starting {settings.PROJECT_NAME} on port 8080...")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(alerts_router)  # Alerts API endpoints
app.include_router(dashboard_router)  # Dashboard API endpoints

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    @app.get("/")
    def serve_frontend():
        """Serve the frontend HTML"""
        return FileResponse(os.path.join(frontend_path, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
