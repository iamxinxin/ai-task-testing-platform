from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.test_models import CallLog, WeeklyPrep
from app.schemas.buffer_schemas import (
    EmergencyShieldRequest,
    EmergencyShieldResponse,
    GeneratePrepRequest,
    GeneratePrepResponse,
    SaveCallLogRequest,
    TranslateShareRequest,
    TranslateShareResponse,
)
from app.services.buffer_service import emergency_shield, generate_prep, translate_share

router = APIRouter()


@router.post("/generate-prep", response_model=GeneratePrepResponse)
async def generate_weekly_prep(payload: GeneratePrepRequest, db: Session = Depends(get_db)):
    result = generate_prep(payload.dread, payload.fatherType, payload.lastCallTopics)
    record = WeeklyPrep(
        user_key="demo-user",
        week_id=result.weekId,
        dread_before=payload.dread,
        predicted_pushes=[item.model_dump() for item in result.predictions],
        selected_shields=[],
    )
    db.add(record)
    db.commit()
    return result


@router.post("/translate-share", response_model=TranslateShareResponse)
async def translate_real_share(payload: TranslateShareRequest):
    return translate_share(payload.rawText, payload.style)


@router.post("/emergency-shield", response_model=EmergencyShieldResponse)
async def get_emergency_shield(payload: EmergencyShieldRequest):
    return emergency_shield(payload.fatherText)


@router.post("/call-log")
async def save_call_log(payload: SaveCallLogRequest, db: Session = Depends(get_db)):
    record = CallLog(
        user_key="demo-user",
        week_id=payload.weekId,
        call_date=datetime.utcnow(),
        dread_after=payload.dreadAfter,
        push_count=payload.pushCount,
        shield_used=payload.shieldUsed,
        shield_effective=payload.shieldEffective,
        notes=payload.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "message": "通话复盘已保存；情绪倾倒箱内容不会上传。"}


@router.get("/stats")
async def get_buffer_stats(db: Session = Depends(get_db)):
    logs = db.query(CallLog).order_by(CallLog.call_date.desc()).limit(4).all()
    trend = [
        {"weekId": item.week_id, "dreadAfter": item.dread_after, "pushCount": item.push_count}
        for item in reversed(logs)
    ]
    current_dread = trend[-1]["dreadAfter"] if trend else 8
    return {"currentDread": current_dread, "trend": trend}
