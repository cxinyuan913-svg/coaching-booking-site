"""公開瀏覽可預約時段（不用登入就能看，送出申請才需要登入）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.timeutil import today_taipei

router = APIRouter(prefix="/api/slots", tags=["slots"])


def _to_out(slot: models.AvailabilitySlot) -> schemas.AvailabilitySlotOut:
    return schemas.AvailabilitySlotOut(
        id=slot.id,
        venue_id=slot.venue_id,
        venue_name=slot.venue.name,
        session_type_id=slot.session_type_id,
        session_type_name=slot.session_type.name,
        duration_minutes=slot.session_type.duration_minutes,
        reference_price=slot.session_type.reference_price,
        date=slot.date,
        start_time=slot.start_time,
        is_booked=slot.is_booked,
    )


@router.get("", response_model=list[schemas.AvailabilitySlotOut])
def list_open_slots(db: Session = Depends(get_db)):
    """只列出「還沒被訂走、日期還沒過」的時段，過去的、已訂走的時段
    不該再讓學生看到能點下去申請。"""
    slots = (
        db.query(models.AvailabilitySlot)
        .filter(
            models.AvailabilitySlot.is_booked.is_(False),
            models.AvailabilitySlot.date >= today_taipei(),
        )
        .order_by(models.AvailabilitySlot.date, models.AvailabilitySlot.start_time)
        .all()
    )
    return [_to_out(slot) for slot in slots]
