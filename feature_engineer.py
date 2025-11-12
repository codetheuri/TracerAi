from app.database import SessionLocal
from app.engineering import process_data_window # Import our new function
from datetime import datetime, timedelta

# This is now just a simple script that *runs* the engineering logic.

if __name__ == "__main__":
    # Create a database session
    db = SessionLocal()
    
    # Define our 10-minute time window
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=3)
    
    print("--- [SCRIPT] Running Feature Engineer ---")
    try:
        # Call the logic from app/engineering.py
        process_data_window(db, start_time, end_time)
    finally:
        db.close()
    print("--- [SCRIPT] Feature Engineer Finished ---")