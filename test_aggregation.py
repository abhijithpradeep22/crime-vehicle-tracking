from backend.app.db.session import SessionLocal
from backend.app.workers.plate_aggregator import aggregate_case_plates

db = SessionLocal()

results = aggregate_case_plates(db, case_id=1)

for r in results:
    print(r)

db.close()
