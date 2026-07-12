from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from ..database import Base

class UVPlaneDay(Base):
    __tablename__ = "uv_plane_days"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    slot_id = Column(Integer, ForeignKey("uv_slots.id"), nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    change_note = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class UVPlaneEntry(Base):
    __tablename__ = "uv_plane_entries"
    id = Column(Integer, primary_key=True, index=True)
    uv_plane_day_id = Column(Integer, ForeignKey("uv_plane_days.id", ondelete="CASCADE"), nullable=False)
    antenna_code = Column(String(10), ForeignKey("antennas.code"), nullable=False)
    status = Column(String(200))
