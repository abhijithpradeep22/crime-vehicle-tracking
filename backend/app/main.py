from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.db.base import Base
from backend.app.db.session import engine

from backend.app.models.camera import Camera
from backend.app.models.case import InvestigationCase
from backend.app.models.sighting import VehicleSighting
from backend.app.api import tracking
from backend.app.api import tracking_routes
from backend.app.api import auth
from backend.app.api.cameras import router as cameras_router
from backend.app.api.cases import router as cases_router
from backend.app.api.sightings import router as sightings_router
from backend.app.api import reports

app = FastAPI(
    title="Crime Vehicle Detection System",
    description="Backend API for multi-camera vehicle tracking",
    version="0.1.0"
)

app.mount("/snapshots", StaticFiles(directory="data/snapshots"), name="snapshots")
app.include_router(cameras_router)
app.include_router(cases_router)
app.include_router(sightings_router)
app.include_router(tracking.router)
app.include_router(tracking_routes.router)
app.include_router(reports.router)
app.include_router(auth.router, prefix="/auth", tags=["Auth"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Crime vehicle tracking backend is running"}

@app.get("/health")
def health_check():
    return {"status": "Ok"}
