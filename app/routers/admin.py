"""教練後台：管理場地／課程時長／開放時段、審核預約申請。全部端點都需要
`is_coach=True`（見 app/auth.py 的 require_coach）。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_coach
from app.booking_tool_client import BookingToolError, create_lesson
from app.database import get_db
from app.models import BookingRequestStatus
from app.routers.bookings import _to_out as booking_to_out

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_coach)])


# ---------- 場地 ----------


@router.get("/venues", response_model=list[schemas.VenueOut])
def list_venues(db: Session = Depends(get_db)):
    return db.query(models.Venue).order_by(models.Venue.id).all()


@router.post("/venues", response_model=schemas.VenueOut, status_code=201)
def create_venue(payload: schemas.VenueCreate, db: Session = Depends(get_db)):
    venue = models.Venue(**payload.model_dump())
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue


# ---------- 課程時長選項 ----------


@router.get("/session_types", response_model=list[schemas.SessionTypeOut])
def list_session_types(db: Session = Depends(get_db)):
    return db.query(models.SessionType).order_by(models.SessionType.id).all()


@router.post("/session_types", response_model=schemas.SessionTypeOut, status_code=201)
def create_session_type(payload: schemas.SessionTypeCreate, db: Session = Depends(get_db)):
    session_type = models.SessionType(**payload.model_dump())
    db.add(session_type)
    db.commit()
    db.refresh(session_type)
    return session_type


@router.patch("/session_types/{session_type_id}", response_model=schemas.SessionTypeOut)
def update_session_type(
    session_type_id: int, payload: schemas.SessionTypeUpdate, db: Session = Depends(get_db)
):
    session_type = db.get(models.SessionType, session_type_id)
    if session_type is None:
        raise HTTPException(status_code=404, detail="課程不存在")
    changes = payload.model_dump(exclude_unset=True)

    # 時段沒有自己存時長，是即時讀課程的 duration_minutes；已經有時段在用時
    # 改時長，會連帶改掉已開放時段跟待審申請的長度（核准時送去教練工具的
    # 也會變），所以擋下來，要不同時長請另外新增一個課程。
    new_duration = changes.get("duration_minutes")
    if new_duration is not None and new_duration != session_type.duration_minutes:
        in_use = (
            db.query(models.AvailabilitySlot)
            .filter(models.AvailabilitySlot.session_type_id == session_type_id)
            .first()
        )
        if in_use is not None:
            raise HTTPException(
                status_code=409,
                detail="這個課程已經有開放時段在用，不能改時長；要不同時長請另外新增一個課程",
            )

    # 名稱、時長、參考價是必填欄位，送 null 視為沒改；說明跟適合對象可以清空
    for field in ("name", "duration_minutes", "reference_price"):
        if changes.get(field, ...) is None:
            changes.pop(field)
    for field, value in changes.items():
        setattr(session_type, field, value)
    db.commit()
    db.refresh(session_type)
    return session_type


# ---------- 開放時段 ----------


@router.get("/slots", response_model=list[schemas.AvailabilitySlotOut])
def list_all_slots(db: Session = Depends(get_db)):
    from app.routers.slots import _to_out as slot_to_out

    slots = (
        db.query(models.AvailabilitySlot)
        .order_by(models.AvailabilitySlot.date, models.AvailabilitySlot.start_time)
        .all()
    )
    return [slot_to_out(s) for s in slots]


@router.post("/slots", response_model=list[schemas.AvailabilitySlotOut], status_code=201)
def batch_create_slots(payload: schemas.AvailabilitySlotBatchCreate, db: Session = Depends(get_db)):
    """依前端選好的一整排日期批次開放時段（見 schemas.AvailabilitySlotBatchCreate
    的說明：日期清單由前端月曆互動組出來，不是後端自己猜規律）。"""
    from app.routers.slots import _to_out as slot_to_out

    venue = db.get(models.Venue, payload.venue_id)
    if venue is None:
        raise HTTPException(status_code=404, detail="場地不存在")
    session_type = db.get(models.SessionType, payload.session_type_id)
    if session_type is None:
        raise HTTPException(status_code=404, detail="課程時長選項不存在")

    created = []
    for slot_date in payload.dates:
        slot = models.AvailabilitySlot(
            venue_id=payload.venue_id,
            session_type_id=payload.session_type_id,
            date=slot_date,
            start_time=payload.start_time,
        )
        db.add(slot)
        created.append(slot)
    db.commit()
    for slot in created:
        db.refresh(slot)
    return [slot_to_out(s) for s in created]


@router.delete("/slots/{slot_id}", status_code=204)
def delete_slot(slot_id: int, db: Session = Depends(get_db)):
    slot = db.get(models.AvailabilitySlot, slot_id)
    if slot is None:
        raise HTTPException(status_code=404, detail="時段不存在")
    if slot.is_booked:
        raise HTTPException(status_code=400, detail="這個時段已經有人約走了，不能直接刪除")
    db.delete(slot)
    db.commit()


# ---------- 預約申請審核 ----------


@router.get("/bookings", response_model=list[schemas.BookingRequestOut])
def list_bookings(status: BookingRequestStatus | None = None, db: Session = Depends(get_db)):
    query = db.query(models.BookingRequest)
    if status is not None:
        query = query.filter(models.BookingRequest.status == status)
    bookings = query.order_by(models.BookingRequest.created_at.desc()).all()
    return [booking_to_out(b, include_user_name=True) for b in bookings]


@router.post("/bookings/{booking_id}/approve", response_model=schemas.BookingRequestOut)
def approve_booking(booking_id: int, db: Session = Depends(get_db)):
    """核准申請：呼叫教練工具建立正式課程成功後，才把這筆標記已核准、
    時段標記已訂走；呼叫失敗的話狀態留在 pending、把錯誤記到 sync_error
    讓教練看得到，之後可以再按一次重試，不會卡在不上不下的中間態。"""
    from datetime import datetime

    booking = db.get(models.BookingRequest, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="申請不存在")
    if booking.status != BookingRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="這筆申請已經處理過了")

    slot = booking.slot
    try:
        create_lesson(
            venue_name=slot.venue.name,
            student_name=booking.user.name,
            student_contact=booking.user.phone or booking.user.email,
            lesson_date=slot.date,
            start_time=slot.start_time,
            duration_minutes=slot.session_type.duration_minutes,
            note=booking.student_note,
        )
    except BookingToolError as exc:
        booking.sync_error = str(exc)
        db.commit()
        db.refresh(booking)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    booking.status = BookingRequestStatus.APPROVED
    booking.decided_at = datetime.now()
    booking.sync_error = None
    slot.is_booked = True

    # 同一個時段如果還有其他人送過申請，這個時段已經被約走了，
    # 其他那些申請自動改成拒絕，不要留著變成看不見的孤兒申請
    other_pending = (
        db.query(models.BookingRequest)
        .filter(
            models.BookingRequest.slot_id == slot.id,
            models.BookingRequest.id != booking.id,
            models.BookingRequest.status == BookingRequestStatus.PENDING,
        )
        .all()
    )
    for other in other_pending:
        other.status = BookingRequestStatus.REJECTED
        other.decided_at = datetime.now()

    db.commit()
    db.refresh(booking)
    return booking_to_out(booking, include_user_name=True)


@router.post("/bookings/{booking_id}/reject", response_model=schemas.BookingRequestOut)
def reject_booking(booking_id: int, db: Session = Depends(get_db)):
    from datetime import datetime

    booking = db.get(models.BookingRequest, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="申請不存在")
    if booking.status != BookingRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="這筆申請已經處理過了")

    booking.status = BookingRequestStatus.REJECTED
    booking.decided_at = datetime.now()
    db.commit()
    db.refresh(booking)
    return booking_to_out(booking, include_user_name=True)
