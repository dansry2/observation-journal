from pydantic import BaseModel
from datetime import date
from typing import Optional

class ErrorEntryItem(BaseModel):
    antenna_code: str
    error_description: Optional[str] = None
    is_broken: bool = False

class ErrorLogCreate(BaseModel):
    date: date
    grid_id: int
    entries: list[ErrorEntryItem]
    change_note: Optional[str] = None
    is_broken: bool = False

class ErrorLogResponse(BaseModel):
    id: int
    date: date
    grid_id: int
    version: int
    entries: list[ErrorEntryItem]
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[str] = None
    change_note: Optional[str] = None
    is_broken: bool = False
    class Config:
        from_attributes = True

class ErrorLogBrief(BaseModel):
    id: int
    date: date
    grid_id: int
    version: int
    is_active: bool
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[str] = None
    change_note: Optional[str] = None
    class Config:
        from_attributes = True

class ErrorLogHistory(BaseModel):
    date: date
    grid_id: int
    versions: list[ErrorLogBrief]
    class Config:
        from_attributes = True
