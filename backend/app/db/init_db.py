from backend.app.db.base import Base
from backend.app.db.session import engine

from backend.app.models.camera import Camera
from backend.app.models.case import InvestigationCase
from backend.app.models.sighting import VehicleSighting
from backend.app.models.tracking_session import TrackingSession
from backend.app.models.report import InvestigationReport


def init_db():
    print("Engine URL:", engine.url)
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables created successfully.")
