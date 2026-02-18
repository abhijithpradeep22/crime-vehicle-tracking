from backend.app.db.base import Base
from backend.app.db.session import engine

from backend.app.models.camera import Camera
from backend.app.models.case import InvestigationCase
from backend.app.models.sighting import VehicleSighting

def init_db():
    Base.metadata.create_all(bind=engine)
