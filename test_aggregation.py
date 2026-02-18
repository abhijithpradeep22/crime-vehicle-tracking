from backend.app.db.session import SessionLocal
from backend.app.workers.plate_aggregator import aggregate_case_plates


def main():
    db = SessionLocal()

    try:
        print("\n===== TESTING PLATE AGGREGATION =====\n")

        case_id = 1  # change if needed
        results = aggregate_case_plates(db, case_id=case_id)

        if not results:
            print("No aggregated results found.")
            return

        print(f"Total clusters found: {len(results)}\n")

        for idx, r in enumerate(results, start=1):
            print(f"Cluster #{idx}")
            print(f"  Primary Plate : {r['primary_plate']}")
            print(f"  Variants      : {r['all_variants']}")
            print(f"  Count         : {r['count']}")
            print(f"  First Seen    : {r['first_seen']}")
            print(f"  Last Seen     : {r['last_seen']}")
            print(f"  Cameras       : {r['cameras']}")
            print("-" * 50)


    except Exception as e:
        print("Error during aggregation test:", str(e))

    finally:
        db.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
