from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class HourlyWeatherItem(BaseModel):
    hour: int
    temperature: Optional[float] = None
    weather_type_id: Optional[int] = None

class EquipmentLogItem(BaseModel):
    equipment_range_id: int
    time_start: Optional[str] = None
    time_stop: Optional[str] = None
    note: Optional[str] = None

class ObservationCreate(BaseModel):
    date: date
    weather: Optional[list[HourlyWeatherItem]] = []
    equipment: Optional[list[EquipmentLogItem]] = []
    duty_user_ids: Optional[list[int]] = []
    change_note: Optional[str] = None
    duty_custom: Optional[str] = None

class ObservationResponse(BaseModel):
    id: int
    date: date
    version: int
    weather: list[HourlyWeatherItem]
    equipment: list[EquipmentLogItem]
    duty_user_ids: list[int]
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    change_note: Optional[str] = None
    duty_custom: Optional[str] = None

    class Config:
        from_attributes = True

class ObservationBrief(BaseModel):
    id: int
    date: date
    version: int
    is_active: bool
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[str] = None
    change_note: Optional[str] = None
    duty_custom: Optional[str] = None

    class Config:
        from_attributes = True

class ObservationHistory(BaseModel):
    date: date
    versions: list[ObservationBrief]

    class Config:
        from_attributes = True
