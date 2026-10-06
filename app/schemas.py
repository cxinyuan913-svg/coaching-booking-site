"""所有 API 的請求/回應格式（Pydantic）。"""
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import BookingRequestStatus, NewsCategory


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
    description: str | None = None
    target_audience: str | None = None


class SessionTypeUpdate(BaseModel):
    """教練後台編輯課程：沒送的欄位維持原值（用 exclude_unset 判斷）。"""

    name: str | None = None
    duration_minutes: int | None = None
    reference_price: float | None = None
    description: str | None = None
    target_audience: str | None = None


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
    # 送出申請當下填的「目前程度」「想加強的地方」，見 models.BookingRequest 的說明
    student_level: str | None = None
    focus_note: str | None = None


class BookingRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: BookingRequestStatus
    student_note: str | None
    student_level: str | None
    focus_note: str | None
    created_at: datetime
    decided_at: datetime | None
    sync_error: str | None
    slot: AvailabilitySlotOut
    user_name: str | None = None  # 教練審核清單才需要看到是誰申請的


def _check_link_url(value: str | None) -> str | None:
    """消息連結會直接放進頁面的 href，只收 http(s)，擋掉 javascript: 之類的；
    空字串視為沒填。"""
    if value is None or not value.strip():
        return None
    value = value.strip()
    if not value.lower().startswith(("http://", "https://")):
        raise ValueError("連結必須是 http:// 或 https:// 開頭")
    return value


class NewsCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    body: str | None = None
    category: NewsCategory = NewsCategory.ANNOUNCEMENT
    link_url: str | None = Field(default=None, max_length=500)
    is_pinned: bool = False
    is_published: bool = True
    # 沒填就用發布當天
    published_on: date | None = None

    @field_validator("link_url")
    @classmethod
    def _validate_link_url(cls, value: str | None) -> str | None:
        return _check_link_url(value)


class NewsUpdate(BaseModel):
    """沒送的欄位維持原值（exclude_unset）；title/category/is_pinned/
    is_published/published_on 送 null 視為沒改，body/link_url 可以清空。"""

    title: str | None = Field(default=None, min_length=1, max_length=100)
    body: str | None = None
    category: NewsCategory | None = None
    link_url: str | None = Field(default=None, max_length=500)
    is_pinned: bool | None = None
    is_published: bool | None = None
    published_on: date | None = None

    @field_validator("link_url")
    @classmethod
    def _validate_link_url(cls, value: str | None) -> str | None:
        return _check_link_url(value)


class NewsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str | None
    category: NewsCategory
    link_url: str | None
    is_pinned: bool
    is_published: bool
    published_on: date
