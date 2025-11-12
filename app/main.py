import joblib
import pandas as pd
import geoip2.database
from fastapi import FastAPI, Depends, Request,  BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from . import crud, models, schemas
from .database import SessionLocal, engine
from .engineering import process_data_window # We import our new logic

# --- 1. CREATE DATABASE TABLES ---
# This will create *both* 'flow_events' and 'host_behavior_summary'
models.Base.metadata.create_all(bind=engine)

# --- 2. LOAD AI MODEL, SCALER, & GEOIP ---
print("--- LOADING AI 'SMART WATCHDOG' (ADVANCED) ---")
try:
    model = joblib.load("host_behavior_model.pkl")
    scaler = joblib.load("host_behavior_scaler.pkl")
    print("--- AI MODEL & SCALER LOADED SUCCESSFULLY ---")
except FileNotFoundError:
    print("--- MODEL/SCALER FILES NOT FOUND! ---")
    print("Please run 'python feature_engineer.py' and 'python train.py' first.")
    model = None
    scaler = None

GEOIP_DB_PATH = "GeoLite2-Country.mmdb"
try:
    geoip_reader = geoip2.database.Reader(GEOIP_DB_PATH)
    print("--- GEOIP DATABASE LOADED SUCCESSFULLY ---")
except FileNotFoundError:
    print(f"--- GEOIP DB NOT FOUND at {GEOIP_DB_PATH} ---")
    geoip_reader = None

# --- 3. SETUP FASTAPI & TEMPLATING ---
app = FastAPI(title="Smart-Trace AI Backend (Advanced)")
templates = Jinja2Templates(directory="templates")

# --- 4. DATABASE DEPENDENCY ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 5. GEOIP HELPER ---
def get_geo_location(ip: str):
    if geoip_reader is None: return "Unknown"
    if ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("127."):
        return "Local"
    try:
        response = geoip_reader.country(ip)
        if response.country.name: return response.country.name
        else: return "Unknown (IP found)"
    except geoip2.errors.AddressNotFoundError: return "Unknown"
    except Exception: return "Error"

# --- 6. THE INGESTION ENDPOINT (Now "Dumb") ---
@app.post("/ingest", response_model=schemas.FlowEvent)
def ingest_single_flow_event(
    event: schemas.FlowEventBase, # Receives the base event from Go
    db: Session = Depends(get_db)
):
    """
    Receives a flow event, enriches it with GeoIP,
    and saves it to the database.
    
    NO AI is run here. This must be FAST.
    """
    
    geo_src = get_geo_location(event.src_ip)
    geo_dst = get_geo_location(event.dst_ip)
    
    enriched_event = schemas.FlowEventCreate(
        **event.model_dump(),
        geo_src=geo_src,
        geo_dst=geo_dst
    )
    
    # Just save the data and return
    db_event = crud.create_flow_event(db=db, event=enriched_event)
    return db_event

# --- 7. NEW ANALYSIS ENDPOINT ---
@app.post("/run-analysis")
async def run_analysis(
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    A *new* endpoint to trigger the 10-minute analysis.
    This runs the feature engineering and AI prediction.
    """
    
    def analyze_and_predict(db_session: Session):
        """ The 'slow' job that runs in the background """
        print("\n--- [ANALYSIS TASK STARTED] ---")
        
        # 1. Define our 10-minute time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=10)
        
        # 2. Run our feature engineering
        # (This loads, aggregates, and saves summaries)
        process_data_window(db_session, start_time, end_time)
        
        # 3. Load the summaries we *just* created
        query = db_session.query(models.HostBehaviorSummary).filter(
            models.HostBehaviorSummary.timestamp >= start_time
        )
        df_summary = pd.read_sql(query.statement, query.session.bind)
        
        if df_summary.empty:
            print("[ANALYSIS TASK] No host summaries to analyze.")
            return

        # 4. Run AI Prediction
        if model and scaler:
            print(f"[ANALYSIS TASK] Predicting on {len(df_summary)} host fingerprints...")
            
            # Prepare the features (must match training!)
            features = [
                'unique_dest_ips', 'unique_dest_ports', 'port_entropy', 
                'country_frequency', 'flow_duration_variance', 
                'total_outbound_bytes', 'total_flows'
            ]
            df_predict = df_summary[features].fillna(0)
            
            # Scale the data *exactly* like we did in training
            df_scaled = scaler.transform(df_predict)
            
            # Get predictions (-1 is anomaly, 1 is normal)
            predictions = model.predict(df_scaled)
            
            # Find the anomalies!
            df_summary['anomaly_score'] = predictions
            anomalies = df_summary[df_summary['anomaly_score'] == -1]
            
            if anomalies.empty:
                print("[ANALYSIS TASK] No anomalies detected.")
            else:
                print(f"🚨🚨🚨 [AI ALERT] {len(anomalies)} ANOMALOUS HOSTS DETECTED! 🚨🚨🚨")
                for _, host in anomalies.iterrows():
                    print(f"  -> Host: {host['host_ip']}")
                    print(f"     Unique Dests: {host['unique_dest_ips']}, Port Entropy: {host['port_entropy']:.2f}")
            
            print("--- [ANALYSIS TASK FINISHED] ---")
        else:
            print("[ANALYSIS TASK] Model/Scaler not loaded. Skipping prediction.")

    # --- This is the API's response ---
    # We add the 'analyze_and_predict' function as a background task.
    # This means the API returns "OK" *immediately* (so it doesn't time out)
    # and the 'slow' job runs after.
    background_tasks.add_task(analyze_and_predict, db)
    return JSONResponse(
        status_code=202, 
        content={"message": "Analysis task accepted and running in background."}
    )


# --- 8. THE DASHBOARD ENDPOINT ---
# (This is unchanged for now, it just shows raw flows)
@app.get("/", response_class=HTMLResponse)
def read_dashboard(request: Request, db: Session = Depends(get_db)):
    events = crud.get_events(db=db, limit=50)
    for event in events:
        event.prediction = 1 # Placeholder
    return templates.TemplateResponse("index.html", {
        "request": request,
        "events": events
    })