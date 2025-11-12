from sqlalchemy import Column, Integer, String, DateTime, Float
from .database import Base

class FlowEvent(Base):
    __tablename__ = "flow_events" 

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    flow_id = Column(String, index=True)
    interface = Column(String)
    hostname = Column(String)
    direction = Column(String, index=True)
    
    src_ip = Column(String, index=True)
    dst_ip = Column(String, index=True)
    src_port = Column(String)
    dst_port = Column(String)
    protocol = Column(String, index=True)

    flow_duration = Column(Float)
    packet_count = Column(Integer)
    byte_count = Column(Integer)
    avg_packet_size = Column(Float)


    geo_src = Column(String, index=True)
    geo_dst = Column(String, index=True)

class HostBehaviorSummary(Base):
    __tablename__ = "host_behavior_summary"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    host_ip = Column(String, index=True)   
    
    unique_dest_ips = Column(Integer)
    unique_dest_ports = Column(Integer)
    port_entropy = Column(Float)
    country_frequency = Column(Float) 
    flow_duration_variance = Column(Float)
    
   
    total_outbound_bytes = Column(Integer)
    total_flows = Column(Integer)
