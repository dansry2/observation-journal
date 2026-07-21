from sqlalchemy import Column, Integer, String, Float, Date, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from ..database import JournalBase as Base

class ObservationDay(Base):
    __tablename__ = "observation_days"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    duty_custom = Column(Text, nullable=True)
    change_note = Column(Text, nullable=True)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class HourlyWeather(Base):
    __tablename__ = "hourly_weather"
    id = Column(Integer, primary_key=True, index=True)
    observation_day_id = Column(Integer, ForeignKey("observation_days.id", ondelete="CASCADE"), nullable=False)
    hour = Column(Integer, nullable=False)
    temperature = Column(Float)
    weather_type_id = Column(Integer, ForeignKey("weather_types.id"))

class EquipmentLog(Base):
    __tablename__ = "equipment_logs"
    id = Column(Integer, primary_key=True, index=True)
    observation_day_id = Column(Integer, ForeignKey("observation_days.id", ondelete="CASCADE"), nullable=False)
    equipment_range_id = Column(Integer, ForeignKey("equipment_ranges.id"), nullable=False)
    time_start = Column(String)
    time_stop = Column(String)
    note = Column(Text)

class ObservationDuty(Base):
    __tablename__ = "observation_duty"
    id = Column(Integer, primary_key=True, index=True)
    observation_day_id = Column(Integer, ForeignKey("observation_days.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, nullable=False)
