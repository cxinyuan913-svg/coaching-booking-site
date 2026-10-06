"""SQLAlchemy ORM models：預約核心五張表一次建齊（比照 coaching-record-tool
的慣例，不分批建立），加上首頁改版時新增的 news（最新消息）。這是全新、
獨立的資料庫，跟 coaching-record-tool 的六張表完全不共用、不同步（見專案
根目錄 CLAUDE.md 的架構決策）。
"""
import enum
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NewsCategory(str, enum.Enum):
    ANNOUNCEMENT = "announcement"  # 公告
    CLASS = "class"  # 開課資訊
    MATCH = "match"  # 賽事成績
    STUDENT = "student"  # 學員成果


class BookingRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # 教練自己的帳號設 True，其他公開註冊的學生帳號一律 False；
    # 後台頁面（管理時段／審核申請）靠這個欄位擋，不是另外一套權限系統
    is_coach: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    booking_requests: Mapped[list["BookingRequest"]] = relationship(back_populates="user")


class Venue(Base):
    """這個新網站自己管理的場地清單，刻意跟 coaching-record-tool 的場地表
    分開、不即時同步（見架構決策：兩個系統互相隔離）。"""

    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str | None] = mapped_column(String(200), nullable=True)

    slots: Mapped[list["AvailabilitySlot"]] = relationship(back_populates="venue")


class SessionType(Base):
    """可預約的課程時長選項（例如「60分鐘」）。reference_price 只是給學生
    預約前參考用的估價，教練核准後實際入帳金額以 coaching-record-tool
    自己的價目表為準，不是從這裡帶過去（避免兩邊價格互相打架）。

    同一張表也服務首頁「課程介紹」卡片的行銷文案（description／
    target_audience），不另外重造一套課程資料——教練後台開時段時選的
    「課程種類」，就是首頁上顯示給學生看的那四張課程卡片。"""

    __tablename__ = "session_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_price: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    # 首頁課程卡片用：課程說明、適合對象。舊資料沒有這兩欄也沒關係
    # （nullable），首頁渲染時空值就不顯示那一行
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_audience: Mapped[str | None] = mapped_column(String(200), nullable=True)

    slots: Mapped[list["AvailabilitySlot"]] = relationship(back_populates="session_type")


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False)
    session_type_id: Mapped[int] = mapped_column(ForeignKey("session_types.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    # 被核准一筆申請後設 True；申請被拒絕要記得改回 False，這個時段才能再被約
    is_booked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    venue: Mapped["Venue"] = relationship(back_populates="slots")
    session_type: Mapped["SessionType"] = relationship(back_populates="slots")
    booking_requests: Mapped[list["BookingRequest"]] = relationship(back_populates="slot")


class BookingRequest(Base):
    __tablename__ = "booking_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    slot_id: Mapped[int] = mapped_column(ForeignKey("availability_slots.id"), nullable=False)
    status: Mapped[BookingRequestStatus] = mapped_column(
        Enum(BookingRequestStatus), nullable=False, default=BookingRequestStatus.PENDING
    )
    student_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 送出申請當下填的「目前程度」「想加強的地方」，是每次預約才會填的
    # 資訊，不是帳號固定屬性，所以放在這裡而不是 User 表
    student_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    focus_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # 核准後呼叫 coaching-record-tool 建立正式課程失敗時，把錯誤訊息記下來，
    # 讓教練在後台看得到「這筆為什麼卡住」，不用去翻 server log
    sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="booking_requests")
    slot: Mapped["AvailabilitySlot"] = relationship(back_populates="booking_requests")


class News(Base):
    """最新消息：首頁跑馬燈、消息輪播與 /news.html 的內容來源，教練在後台
    發布。is_published=False 是草稿或已下架，公開 API 一律看不到；
    is_pinned 的排在最前面（跑馬燈跟輪播都會優先顯示）。"""

    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[NewsCategory] = mapped_column(
        Enum(NewsCategory), nullable=False, default=NewsCategory.ANNOUNCEMENT
    )
    # 選填的外部連結（例如報名表單、比賽報導、IG 貼文）
    link_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # 顯示在消息上的日期，教練可以自己指定（例如比賽當天），預設發布當天
    published_on: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
