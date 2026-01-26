from fastapi import FastAPI
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.api.cameras import router as cameras_router
from backend.app.api.cases import router as cases_router


app = FastAPI(
    title="Crime Vehicle Detection System",
    description="Backend API for multi-camera vehicle tracking",
    version="0.1.0"
)

app.include_router(cameras_router)
app.include_router(cases_router)

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Crime vehicle tracking backend is running"}

@app.get("/health")
def health_check():
    return {"status": "Ok"}
