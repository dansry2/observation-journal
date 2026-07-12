from pydantic import BaseModel
from datetime import date
from typing import Optional

class ErrorEntryItem(BaseModel):
    antenna_code: str
    error_description: Optional[str] = None

class ErrorLogCreate(BaseModel):
    date: date
    grid_id: int
    entries: list[ErrorEntryItem]

class ErrorLogResponse(BaseModel):
    id: Optional[int] = None
    date: date
    grid_id: int
    entries: list[ErrorEntryItem]
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    class Config:
        from_attributes = True

class MovementItem(BaseModel):
    component_name: str
    from_antenna: Optional[str] = None
    to_antenna: Optional[str] = None
    note: Optional[str] = None

class MovementCreate(BaseModel):
    date: date
    movements: list[MovementItem]

class MovementResponse(BaseModel):
    id: Optional[int] = None
    date: date
    movements: list[MovementItem]
    created_by: Optional[str] = None
    class Config:
        from_attributes = True

class AntennaNoteItem(BaseModel):
    antenna_code: str
    note: Optional[str] = None

class AntennaNoteCreate(BaseModel):
    date: date
    notes: list[AntennaNoteItem]

class AntennaNoteResponse(BaseModel):
    id: Optional[int] = None
    date: date
    notes: list[AntennaNoteItem]
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    class Config:
        from_attributes = True

class DailyNoteCreate(BaseModel):
    date: date
    title: Optional[str] = None
    description: Optional[str] = None

class DailyNoteResponse(BaseModel):
    id: int
    date: date
    title: Optional[str] = None
    description: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    class Config:
        from_attributes = True
