from pydantic import BaseModel
from datetime import date
from typing import Optional

class UVPlaneEntryItem(BaseModel):
    antenna_code: str
    status: Optional[str] = None

class UVPlaneCreate(BaseModel):
    date: date
    slot_id: int
    entries: list[UVPlaneEntryItem]
    change_note: Optional[str] = None

class UVPlaneResponse(BaseModel):
    id: int
    date: date
    slot_id: int
    version: int
    entries: list[UVPlaneEntryItem]
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[str] = None
    change_note: Optional[str] = None

    class Config:
        from_attributes = True

class UVPlaneBrief(BaseModel):
    id: int
    date: date
    slot_id: int
    version: int
    is_active: bool
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[str] = None
    change_note: Optional[str] = None

    class Config:
        from_attributes = True

class UVPlaneHistory(BaseModel):
    date: date
    slot_id: int
    versions: list[UVPlaneBrief]

    class Config:
        from_attributes = True
