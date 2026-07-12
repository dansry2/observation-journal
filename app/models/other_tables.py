from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from ..database import Base

class ComponentMovement(Base):
    __tablename__ = "component_movements"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    component_name = Column(String(200), nullable=False)
    from_antenna = Column(String(10), ForeignKey("antennas.code"), nullable=True)
    to_antenna = Column(String(10), ForeignKey("antennas.code"), nullable=True)
    note = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    __table_args__ = (CheckConstraint("from_antenna IS NOT NULL OR to_antenna IS NOT NULL"),)

class AntennaNote(Base):
    __tablename__ = "antenna_notes"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    antenna_code = Column(String(10), ForeignKey("antennas.code"), nullable=False)
    note = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint("date", "antenna_code"),)

class DailyNote(Base):
    __tablename__ = "daily_notes"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    title = Column(String(200))
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
