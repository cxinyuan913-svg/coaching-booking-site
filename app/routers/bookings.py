"""學生送出預約申請、查自己送出過的申請（都需要登入）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_user
from app.database import get_db
from app.notifications import send_discord_notification
from app.routers.slots import _to_out as slot_to_out

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def _to_out(request: models.BookingRequest, *, include_user_name: bool = False) -> schemas.BookingRequestOut:
    return schemas.BookingRequestOut(
        id=request.id,
        status=request.status,
        student_note=request.student_note,
        created_at=request.created_at,
        decided_at=request.decided_at,
        sync_error=request.sync_error,
        slot=slot_to_out(request.slot),
        user_name=request.user.name if include_user_name else None,
    )


@router.post("", response_model=schemas.BookingRequestOut, status_code=201)
def create_booking(
    payload: schemas.BookingRequestCreate,
    user: models.User = Depends(require_user),
    db: Session = Depends(get_db),
):
    slot = db.get(models.AvailabilitySlot, payload.slot_id)
    if slot is None:
        raise HTTPException(status_code=404, detail="時段不存在")
    if slot.is_booked:
        raise HTTPException(status_code=400, detail="這個時段已經被約走了")

    booking = models.BookingRequest(
        user_id=user.id,
        slot_id=slot.id,
        student_note=payload.student_note,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    send_discord_notification(
        f"📅 新的預約申請\n"
        f"{user.name}\n"
        f"{slot.date.isoformat()} {slot.start_time.strftime('%H:%M')}"
        f"（{slot.venue.name}，{slot.session_type.name}）\n"
        f"請到後台審核"
    )
    return _to_out(booking)


@router.get("", response_model=list[schemas.BookingRequestOut])
def list_my_bookings(user: models.User = Depends(require_user), db: Session = Depends(get_db)):
    bookings = (
        db.query(models.BookingRequest)
        .filter(models.BookingRequest.user_id == user.id)
        .order_by(models.BookingRequest.created_at.desc())
        .all()
    )
    return [_to_out(b) for b in bookings]
