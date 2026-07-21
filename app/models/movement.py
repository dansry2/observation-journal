from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from ..database import JournalBase as Base

class MovementDay(Base):
    __tablename__ = "movement_days"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    change_note = Column(Text, nullable=True)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class MovementEntry(Base):
    __tablename__ = "movement_entries"
    id = Column(Integer, primary_key=True, index=True)
    movement_day_id = Column(Integer, ForeignKey("movement_days.id", ondelete="CASCADE"), nullable=False)
    component_name = Column(String(200), nullable=False)
    from_antenna = Column(String(10), nullable=True)
    to_antenna = Column(String(10), nullable=True)
    note = Column(Text)
