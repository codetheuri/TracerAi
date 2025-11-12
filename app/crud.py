from sqlalchemy.orm import Session
from . import models, schemas



def create_flow_event(db: Session, event: schemas.FlowEventBase):
    """
    Takes a FlowEventBase Pydantic schema and saves it
    to the database as a FlowEvent model.
    """
    db_event = models.FlowEvent(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_events(db: Session, skip: int = 0, limit: int = 50):
    """
    Retrieves the 50 most recent flow events.
    """
    return db.query(models.FlowEvent).order_by(models.FlowEvent.id.desc()).offset(skip).limit(limit).all()