from pydantic import BaseModel
from datetime import date
from typing import Optional

class MovementItem(BaseModel):
    component_name: str
    from_antenna: Optional[str] = None
    to_antenna: Optional[str] = None
    note: Optional[str] = None

class MovementCreate(BaseModel):
    date: date
    movements: list[MovementItem]
    change_note: Optional[str] = None

class MovementResponse(BaseModel):
    id: int
    date: date
    version: int
    movements: list[MovementItem]
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[str] = None
    change_note: Optional[str] = None
    class Config:
        from_attributes = True

class MovementBrief(BaseModel):
    id: int
    date: date
    version: int
    is_active: bool
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[str] = None
    change_note: Optional[str] = None
    class Config:
        from_attributes = True

class MovementHistory(BaseModel):
    date: date
    versions: list[MovementBrief]
    class Config:
        from_attributes = True
