from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..database import JournalBase as Base

class WeatherType(Base):
    __tablename__ = "weather_types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)

class FrequencyRange(Base):
    __tablename__ = "frequency_ranges"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), nullable=False, unique=True)

class Antenna(Base):
    __tablename__ = "antennas"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    frequency_range_id = Column(Integer, ForeignKey("frequency_ranges.id"), nullable=True)
    sort_order = Column(Integer, default=0)

class EquipmentRange(Base):
    __tablename__ = "equipment_ranges"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)

class UVSlot(Base):
    __tablename__ = "uv_slots"
    id = Column(Integer, primary_key=True, index=True)
    slot_time = Column(String(10), nullable=False, unique=True)

class UVStatus(Base):
    __tablename__ = "uv_statuses"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(100), nullable=False, unique=True)
