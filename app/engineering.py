import pandas as pd
from sqlalchemy.orm import Session
from scipy.stats import entropy
from datetime import datetime
from . import models # Use relative import

# --- HELPER FUNCTIONS ---

def calculate_port_entropy(ports):
    """Calculates the entropy of the port distribution."""
    counts = ports.value_counts(normalize=True)
    return entropy(counts)

def calculate_country_frequency(countries):
    """Calculates the ratio of unique countries to total flows."""
    if len(countries) == 0:
        return 0.0
    unique_countries = countries.nunique()
    return float(unique_countries) / len(countries)

# --- MAIN LOGIC ---

def process_data_window(db_session: Session, start_time: datetime, end_time: datetime):
    """
    Main function to process all 'flow_events' in a time window
    and create 'host_behavior_summary' records.
    """
    
    # --- 1. LOAD RAW FLOWS ---
    print(f"Loading raw flows from {start_time} to {end_time}...")
    query = db_session.query(models.FlowEvent).filter(
        models.FlowEvent.timestamp >= start_time,
        models.FlowEvent.timestamp < end_time,
        models.FlowEvent.direction == 'outbound'
    )
    df = pd.read_sql(query.statement, query.session.bind)
    
    if df.empty:
        print("No new flow data to process.")
        return

    print(f"Loaded {len(df)} outbound flows.")

    # --- 2. AGGREGATE & CALCULATE FEATURES ---
    print("Aggregating flows and calculating advanced features...")
    
    host_summary = df.groupby('src_ip').agg(
        unique_dest_ips=('dst_ip', 'nunique'),
        unique_dest_ports=('dst_port', 'nunique'),
        port_entropy=('dst_port', calculate_port_entropy),
        country_frequency=('geo_dst', calculate_country_frequency),
        flow_duration_variance=('flow_duration', 'var'),
        total_outbound_bytes=('byte_count', 'sum'),
        total_flows=('flow_id', 'count')
    ).reset_index()

    host_summary = host_summary.fillna(0)
    print(f"Created summaries for {len(host_summary)} hosts.")

    # --- 3. SAVE SUMMARIES TO NEW TABLE ---
    summary_timestamp = datetime.now()
    saved_count = 0
    
    for _, row in host_summary.iterrows():
        summary_record = models.HostBehaviorSummary(
            timestamp=summary_timestamp,
            host_ip=row['src_ip'],
            unique_dest_ips=row['unique_dest_ips'],
            unique_dest_ports=row['unique_dest_ports'],
            port_entropy=row['port_entropy'],
            country_frequency=row['country_frequency'],
            flow_duration_variance=row['flow_duration_variance'],
            total_outbound_bytes=row['total_outbound_bytes'],
            total_flows=row['total_flows']
        )
        db_session.add(summary_record)
        saved_count += 1
        
    db_session.commit()
    print(f"Successfully saved {saved_count} host behavior summaries to the database.")