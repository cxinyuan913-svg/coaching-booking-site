"""所有 API 的請求/回應格式（Pydantic）。"""
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import BookingRequestStatus


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str
    phone: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    phone: str | None
    is_coach: bool


class VenueCreate(BaseModel):
    name: str
    address: str | None = None


class VenueOut(VenueCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class SessionTypeCreate(BaseModel):
    name: str
    duration_minutes: int
    reference_price: float = 0


class SessionTypeOut(SessionTypeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class AvailabilitySlotBatchCreate(BaseModel):
    """批次開放時段：比照 coaching-record-tool 套組建立畫面「先選一整排日期，
    再手動點掉不要的」的模式，dates 由前端月曆互動組出來，不是後端猜規律。"""

    venue_id: int
    session_type_id: int
    dates: list[date]
    start_time: time


class AvailabilitySlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    venue_id: int
    venue_name: str
    session_type_id: int
    session_type_name: str
    duration_minutes: int
    reference_price: float
    date: date
    start_time: time
    is_booked: bool


class BookingRequestCreate(BaseModel):
    slot_id: int
    student_note: str | None = None


class BookingRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: BookingRequestStatus
    student_note: str | None
    created_at: datetime
    decided_at: datetime | None
    sync_error: str | None
    slot: AvailabilitySlotOut
    user_name: str | None = None  # 教練審核清單才需要看到是誰申請的
