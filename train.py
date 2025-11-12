import pandas as pd
import joblib
from sqlalchemy import create_engine
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

print("--- Training on Advanced Host Behavior ---")


engine = create_engine("sqlite:///./smart-trace.db")
print("Loading data from 'host_behavior_summary' table...")

try:
   
    df = pd.read_sql_table("host_behavior_summary", con=engine)
except ValueError:
    print("Error: 'host_behavior_summary' table not found or empty.")
    print("Please run 'feature_engineer.py' to create the summary data first.")
    exit()

if df.empty:
    print("DataFrame is empty. No data to train on. Exiting.")
    exit()

print(f"Loaded {len(df)} host summary records.")


print("Preparing data for AI...")

features_to_train = [
    'unique_dest_ips',
    'unique_dest_ports',
    'port_entropy',
    'country_frequency',
    'flow_duration_variance',
    'total_outbound_bytes',
    'total_flows'
]
df_features = df[features_to_train].copy()



print("Scaling features...")
scaler = StandardScaler()

df_scaled = scaler.fit_transform(df_features)

model = IsolationForest(
    n_estimators=100,
    contamination='auto',
    random_state=42
)

print("Training AI 'Watchdog' on the new feature set...")
model.fit(df_scaled) 
print("Training complete!")


joblib.dump(model, "host_behavior_model.pkl")
joblib.dump(scaler, "host_behavior_scaler.pkl")

print("---------------------------------------------------------")
print("✅ Success! Your NEW Advanced 'Host Watchdog' AI is trained.")
print("Two files have been created:")
print("  1. host_behavior_model.pkl (The new trained AI model)")
print("  2. host_behavior_scaler.pkl (The new data scaler)")
print("---------------------------------------------------------")