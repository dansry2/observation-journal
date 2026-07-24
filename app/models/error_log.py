from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from ..database import JournalBase as Base

class ErrorLogDay(Base):
    __tablename__ = "error_log_days"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    grid_id = Column(Integer, ForeignKey("equipment_ranges.id"), nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    is_broken = Column(Boolean, default=False)
    change_note = Column(Text, nullable=True)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ErrorLogEntry(Base):
    __tablename__ = "error_log_entries"
    id = Column(Integer, primary_key=True, index=True)
    error_log_day_id = Column(Integer, ForeignKey("error_log_days.id", ondelete="CASCADE"), nullable=False)
    antenna_code = Column(String(10), ForeignKey("antennas.code"), nullable=False)
    error_description = Column(Text)
    is_broken = Column(Boolean, default=False)
