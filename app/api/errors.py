import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from ..models.error_log import ErrorLogDay, ErrorLogEntry
from ..database import get_user_name
from ..models.user import User
from ..schemas.error_log import ErrorLogCreate, ErrorLogResponse, ErrorLogBrief, ErrorLogHistory
from ..utils.deps import get_current_user, get_optional_user, get_optional_user, get_active_user, get_optional_user

router = APIRouter(prefix="/errors-grid", tags=["errors"])
@router.post("/check-conflicts", response_model=None)
def check_conflicts(data: ErrorLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    active = db.query(ErrorLogDay).filter(
        ErrorLogDay.date == data.date, ErrorLogDay.grid_id == data.grid_id, ErrorLogDay.is_active == True
    ).first()
    if not active:
        return {"conflict": False}
    
    old_errors = {}
    for e in db.query(ErrorLogEntry).filter(ErrorLogEntry.error_log_day_id == active.id).all():
        if e.error_description is not None:
            old_errors[e.antenna_code] = e.error_description
    
    for e in (data.entries or []):
        if e.antenna_code in old_errors and e.error_description is not None and e.error_description != old_errors[e.antenna_code]:
            return {"conflict": True}
    
    return {"conflict": False}


def _merge_and_create(data: ErrorLogCreate, db: Session, current_user: User):
    active = db.query(ErrorLogDay).filter(
        ErrorLogDay.date == data.date,
        ErrorLogDay.grid_id == data.grid_id,
        ErrorLogDay.is_active == True
    ).first()

    # Деактивируем ВСЕ активные дни этого grid_id (кроме текущего)
    prev_days = db.query(ErrorLogDay).filter(
        ErrorLogDay.grid_id == data.grid_id,
        ErrorLogDay.is_active == True,
        ErrorLogDay.date != data.date
    ).all()
    for pd in prev_days:
        pd.is_active = False
    if prev_days:
        db.flush()

    # Удаляем entries деактивированных дней с датой > текущей (они устарели)
    future_days = db.query(ErrorLogDay).filter(
        ErrorLogDay.grid_id == data.grid_id,
        ErrorLogDay.date > data.date,
        ErrorLogDay.is_active == False
    ).all()
    for fd in future_days:
        db.query(ErrorLogEntry).filter(ErrorLogEntry.error_log_day_id == fd.id).delete()
        db.delete(fd)
    if future_days:
        db.flush()

    new_version = 1
    old_entries = {}

    if active:
        new_version = active.version + 1
        active.is_active = False
        for e in db.query(ErrorLogEntry).filter(ErrorLogEntry.error_log_day_id == active.id).all():
            old_entries[e.antenna_code] = (e.error_description, e.is_ok, e.start_time, e.end_time, e.events_json)
        db.flush()

    day = ErrorLogDay(
        date=data.date, grid_id=data.grid_id, version=new_version,
        is_ok=data.is_ok,
        is_active=True, change_note=data.change_note,
        created_by=current_user.id, updated_by=current_user.id
    )
    db.add(day)
    db.flush()

    new_entries = {}
    for e in (data.entries or []):
        events_json = None
        if e.events:
            events_json = json.dumps([ev.dict() for ev in e.events], ensure_ascii=False)
        new_entries[e.antenna_code] = (e.error_description, e.is_ok, e.start_time, e.end_time, events_json)

    all_antennas = set(list(old_entries.keys()) + list(new_entries.keys()))
    for code in all_antennas:
        if code in new_entries:
            desc, is_ok, start_time, end_time, events_json = new_entries[code]
        else:
            desc, is_ok, start_time, end_time, events_json = old_entries.get(code, (None, True, None, None, None))

        # Если антенна починена и есть открытая поломка - закрываем её
        if is_ok and end_time:
            for old_entry in db.query(ErrorLogEntry).join(ErrorLogDay).filter(
                ErrorLogEntry.antenna_code == code,
                ErrorLogEntry.is_ok == False,
                ErrorLogEntry.end_time == None
            ).all():
                # Сохраняем оригинальный broken_since
                original_broken_since = old_entry.broken_since
                # Обновляем исходную запись: добавляем время конца и дату починки
                old_entry.end_time = end_time
                old_entry.broken_until = str(day.date)
                broken_since = original_broken_since or str(day.date)

        # Валидация: restore без breakdown
        if events_json:
            try:
                evs = json.loads(events_json)
            except Exception:
                evs = []
            has_restore = any(ev.get("type") == "restore" for ev in evs)
            has_breakdown = any(ev.get("type") == "breakdown" for ev in evs)
            if has_restore and not has_breakdown:
                raise HTTPException(status_code=400, detail=f"У антенны {code} есть восстановление, но нет поломки")

        broken_until_value = str(day.date) if end_time else None
        db.add(ErrorLogEntry(
            error_log_day_id=day.id, 
            antenna_code=code, 
            error_description=desc, 
            is_ok=is_ok, 
            start_time=start_time, 
            end_time=end_time, 
            broken_since=broken_since if 'broken_since' in locals() else str(day.date),
            broken_until=broken_until_value,
            events_json=events_json
        ))

    db.commit()
    db.refresh(day)
    return day

@router.post("/", response_model=ErrorLogResponse)
def create_or_update(data: ErrorLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    day = _merge_and_create(data, db, current_user)
    return _build_response(day, db)

@router.delete("/entry/{day_id}/{antenna_code}")
def delete_entry(day_id: int, antenna_code: str, db: Session = Depends(get_db), current_user = Depends(get_active_user)):
    from datetime import datetime as dt

    # Находим все активные записи с этой антенной (включая предыдущие дни)
    all_entries = db.query(ErrorLogEntry).join(ErrorLogDay).filter(
        ErrorLogEntry.antenna_code == antenna_code
    ).all()

    # Добавляем запись из текущего day_id, если её нет в списке
    target_entry = db.query(ErrorLogEntry).filter(
        ErrorLogEntry.error_log_day_id == day_id,
        ErrorLogEntry.antenna_code == antenna_code
    ).first()
    if target_entry and target_entry not in all_entries:
        all_entries.append(target_entry)

    if not all_entries:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    deleted_event = {
        "id": f"del-{dt.now().timestamp()}",
        "type": "deleted",
        "date": dt.now().strftime("%Y-%m-%d"),
        "time": dt.now().strftime("%H:%M"),
        "note": "удалено пользователем"
    }

    for entry in all_entries:
        events = []
        if entry.events_json:
            try:
                events = json.loads(entry.events_json)
            except Exception:
                events = []
        events.append(deleted_event)
        entry.events_json = json.dumps(events, ensure_ascii=False)
        entry.is_ok = True

    db.commit()
    return {"ok": True, "deleted": antenna_code, "affected": len(all_entries)}


@router.get("/check-next-days/{obs_date}/{grid_id}")
def check_next_days(obs_date: date, grid_id: int, db: Session = Depends(get_db)):
    next_days = db.query(ErrorLogDay).filter(
        ErrorLogDay.grid_id == grid_id,
        ErrorLogDay.date > obs_date,
        ErrorLogDay.is_active == True
    ).order_by(ErrorLogDay.date).all()

    result = []
    for day in next_days:
        entries = db.query(ErrorLogEntry).filter(ErrorLogEntry.error_log_day_id == day.id).all()
        has_restore = False
        for e in entries:
            if e.events_json:
                try:
                    evs = json.loads(e.events_json)
                    if any(ev.get("type") == "restore" for ev in evs):
                        has_restore = True
                        break
                except Exception:
                    pass
        if has_restore:
            result.append(str(day.date))

    return {"next_dates": result}


@router.get("/{obs_date}/{grid_id}", response_model=ErrorLogResponse)
def get_active(obs_date: date, grid_id: int, db: Session = Depends(get_db), current_user = Depends(get_optional_user)):
    day = db.query(ErrorLogDay).filter(
        ErrorLogDay.date == obs_date, ErrorLogDay.grid_id == grid_id,
        ErrorLogDay.is_active == True
    ).first()

    
    if not day:
        # Нет активной — берём последнюю версию за эту дату (для истории)
        day = db.query(ErrorLogDay).filter(
            ErrorLogDay.date == obs_date, ErrorLogDay.grid_id == grid_id
        ).order_by(ErrorLogDay.version.desc(), ErrorLogDay.id.desc()).first()

    if not day:
        open_entries = _get_open_entries(db, obs_date, grid_id)
        if not open_entries:
            raise HTTPException(status_code=404, detail="Not found")

        # Деактивируем старые записи дней, откуда переносим
        old_day_ids = set()
        for e in open_entries:
            old_day = db.query(ErrorLogDay).filter(ErrorLogDay.id == e.error_log_day_id).first()
            if old_day and old_day.date < obs_date:
                old_day_ids.add(old_day.id)
        for old_day_id in old_day_ids:
            old_day = db.query(ErrorLogDay).filter(ErrorLogDay.id == old_day_id).first()
            if old_day:
                old_day.is_active = False

        # Деактивируем ВСЕ активные дни этого grid_id (кроме создаваемого)
        to_deactivate = db.query(ErrorLogDay).filter(
            ErrorLogDay.grid_id == grid_id,
            ErrorLogDay.is_active == True,
            ErrorLogDay.date != obs_date
        ).all()
        for td in to_deactivate:
            td.is_active = False
        if to_deactivate:
            db.flush()

        day = ErrorLogDay(date=obs_date, grid_id=grid_id, version=0, is_active=True)
        db.add(day)
        db.flush()
        for e in open_entries:
            broken_date = e.broken_since or str(day.date)
            events = []
            if e.events_json:
                try:
                    events = json.loads(e.events_json)
                except Exception:
                    events = []
            active_events = _get_active_events(events)
            if not active_events:
                continue
            active_events_json = json.dumps(active_events, ensure_ascii=False)
            db.add(ErrorLogEntry(
                error_log_day_id=day.id,
                antenna_code=e.antenna_code,
                error_description=e.error_description,
                is_ok=e.is_ok,
                start_time=e.start_time,
                end_time=e.end_time,
                broken_since=broken_date,
                events_json=active_events_json
            ))
        db.commit()
    
    return _build_response(day, db)

@router.get("/{obs_date}/{grid_id}/history", response_model=ErrorLogHistory)
def get_history(obs_date: date, grid_id: int, db: Session = Depends(get_db), current_user = Depends(get_optional_user)):
    versions = db.query(ErrorLogDay).filter(
        ErrorLogDay.date == obs_date, ErrorLogDay.grid_id == grid_id
    ).order_by(ErrorLogDay.version.desc()).all()

    if not versions:
        raise HTTPException(status_code=404, detail="Not found")

    result = []
    for v in versions:
        creator_name = get_user_name(v.created_by)
        updater_name = get_user_name(v.updated_by)
        result.append(ErrorLogBrief(
            id=v.id, date=v.date, grid_id=v.grid_id, version=v.version,
            is_active=v.is_active,
            created_by=creator_name,
            updated_by=updater_name,
            created_at=str(v.created_at), change_note=v.change_note
        ))
    return ErrorLogHistory(date=obs_date, grid_id=grid_id, versions=result)

def _has_open_breakdown(entry):
    if entry.events_json:
        try:
            events = json.loads(entry.events_json)
        except Exception:
            events = []
        balance = 0
        has_deleted = False
        for ev in events:
            if ev.get("type") == "breakdown":
                balance += 1
            elif ev.get("type") == "restore":
                balance -= 1
            elif ev.get("type") == "deleted":
                has_deleted = True
            elif ev.get("type") == "other" and not ev.get("date_end"):
                return True
        if has_deleted:
            return False
        return balance > 0
    return entry.is_ok == False and entry.end_time is None


def _get_active_events(events):
    """Оставляет открытые other + события после последнего закрытия баланса."""
    if not events:
        return []
    balance = 0
    last_zero_idx = -1
    for i, ev in enumerate(events):
        if ev.get("type") == "breakdown":
            balance += 1
        elif ev.get("type") == "restore":
            balance -= 1
        elif ev.get("type") == "deleted":
            last_zero_idx = i
            continue
        if balance == 0:
            last_zero_idx = i

    result = list(events[last_zero_idx + 1:])

    # Открытые other из истории до last_zero_idx, но не после deleted
    for i, ev in enumerate(events[:last_zero_idx + 1]):
        if ev.get("type") == "other" and not ev.get("date_end"):
            has_deleted_after = any(
                e.get("type") == "deleted" for e in events[i+1:last_zero_idx+1]
            )
            if not has_deleted_after:
                result.insert(0, ev)

    return result


def _get_open_entries(db, date, grid_id):
    # Активный день — приоритет
    active_day = db.query(ErrorLogDay).filter(
        ErrorLogDay.date < date,
        ErrorLogDay.grid_id == grid_id,
        ErrorLogDay.is_active == True
    ).order_by(ErrorLogDay.date.desc()).first()

    if active_day:
        entries = db.query(ErrorLogEntry).filter(ErrorLogEntry.error_log_day_id == active_day.id).all()
        result = []
        for e in entries:
            evs = []
            if e.events_json:
                try:
                    evs = json.loads(e.events_json)
                except Exception:
                    evs = []
            active_events = _get_active_events(evs)
            if not active_events:
                continue

            result.append(e)
        return result

    # Нет активного — ищем по всем
    candidates = db.query(ErrorLogEntry, ErrorLogDay.date).join(ErrorLogDay).filter(
        ErrorLogDay.date < date,
        ErrorLogDay.grid_id == grid_id
    ).order_by(ErrorLogDay.date.desc(), ErrorLogEntry.id.desc()).all()

    latest_by_antenna = {}
    for entry, d in candidates:
        if entry.antenna_code not in latest_by_antenna:
            latest_by_antenna[entry.antenna_code] = entry

    open_entries = []
    for entry in latest_by_antenna.values():
        if _has_open_breakdown(entry):
            events = []
            if entry.events_json:
                try:
                    events = json.loads(entry.events_json)
                except Exception:
                    events = []
            if _get_active_events(events):
                open_entries.append(entry)
    return open_entries


def _build_response(day, db):
    entries = db.query(ErrorLogEntry).filter(ErrorLogEntry.error_log_day_id == day.id).all()
    open_entries = _get_open_entries(db, day.date, day.grid_id)

    # Сначала open_entries (из прошлых дней), потом перезаписываем записями текущего дня
    latest_by_antenna = {}
    for e in open_entries:
        latest_by_antenna[e.antenna_code] = e
    for e in entries:
        latest_by_antenna[e.antenna_code] = e
    unique_entries = list(latest_by_antenna.values())

    entries_result = []
    for e in unique_entries:
        events = None
        if getattr(e, 'events_json', None):
            try:
                events = json.loads(e.events_json)
            except Exception:
                events = None

        entry = {
            "antenna_code": e.antenna_code,
            "error_description": e.error_description,
            "is_ok": e.is_ok,
            "start_time": e.start_time,
            "end_time": e.end_time,
            "broken_since": getattr(e, 'broken_since', None) or str(day.date),
            "events": events,
            "day_id": e.error_log_day_id
        }
        if e.end_time:
            entry["broken_until"] = getattr(e, 'broken_until', None) or str(day.date)
        if not e.is_ok:
            entry["broken_since"] = e.broken_since or str(day.date)
        entries_result.append(entry)

    return {
        "id": day.id, "date": day.date, "grid_id": day.grid_id, "version": day.version,
        "entries": entries_result,
        "created_at": str(day.created_at), "change_note": day.change_note,
        "is_ok": day.is_ok
    }



