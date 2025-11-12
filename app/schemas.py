import datetime
from pydantic import BaseModel
from typing import Optional


class FlowEventBase(BaseModel):
    flow_id: str
    timestamp: datetime.datetime
    interface: str
    hostname: str
    direction: str
    
    src_ip: str
    dst_ip: str
    src_port: str
    dst_port: str
    protocol: str
    
    flow_duration: float
    packet_count: int
    byte_count: int
    avg_packet_size: float


class FlowEventCreate(FlowEventBase):
  
    geo_src: str
    geo_dst: str

class FlowEvent(FlowEventCreate):
    id: int

    class Config:
        from_attributes = True