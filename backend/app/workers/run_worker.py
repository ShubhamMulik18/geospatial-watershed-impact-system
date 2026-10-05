import time

from app.db.session import SessionLocal
from app.workers.analysis_worker import AnalysisWorker


def main() -> None:
    db = SessionLocal()
    worker = AnalysisWorker(db=db)

    try:
        while True:
            processed = worker.run_once()

            if not processed:
                time.sleep(worker.poll_interval_seconds)

    except KeyboardInterrupt:
        print("Analysis worker stopped.")

    finally:
        db.close()


if __name__ == "__main__":
    main()