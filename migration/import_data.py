"""
Миграция данных из Excel в observation-journal.

Книга1.xlsx — журнал ошибок антенн
Книга2.xlsx — журнал наблюдений (погода + статус оборудования)

Запуск: python3 migration/import_data.py
"""
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import JournalSessionLocal, JournalBase, journal_engine
from app.models import *  # noqa
from app.models.error_log import ErrorLogDay, ErrorLogEntry
from app.models.observation import (
    ObservationDay, HourlyWeather, EquipmentLog, ObservationDuty
)
from app.references import ANTENNAS, WEATHER_TYPES


# ============ СООТВЕТСТВИЯ ============

# Диапазоны из Книги 1

def normalize_grid_name(s):
    if not s or (isinstance(s, float) and pd.isna(s)):
        return None
    s = str(s).strip()
    s = s.replace("_", "-")
    s = re.sub(r"^0+", "", s)
    s = re.sub(r"\s+", "", s)
    return s

GRID_NAME_TO_ID = {
    "3-6GHz": 5, "3-6ГГц": 5,
    "6-12GHz": 6, "6-12ГГц": 6,
    "12-24GHz": 7, "12-24ГГц": 7,
}

# Диапазоны из Книги 2 (порядок столбцов)
# (начало_столбца, имя, equipment_range_id или None)
EQUIPMENT_RANGES = [
    (23, "4-8 ГГц", 1),
    (26, "Calisto", 2),
    (29, "0,05-3 Ггц", 3),
    (32, "3-24 Ггц", 4),
    (35, "3-6 Ггц", 5),
    (38, "6-12 Ггц", 6),
    (41, "12-24 Ггц", 7),
    # 44 — Дежурные
    # 45-47 — 2-24 ГГц — пропускаем (нет в справочнике)
]

# Нормализация погоды → weather_type_id
WEATHER_MAP = {
    "ясно": 1, "солнце": 1, "солнечно": 1, "ясн": 1,
    "облачно": 2, "обл": 2, "облач": 2,
    "дождь": 3, "дождик": 3, "дожди": 3, "ливень": 3,
    "снег": 4, "снежок": 4, "порошка": 4, "порош": 4,
    "туман": 5, "тума": 5,
    "пасмурно": 6, "пасм": 6, "пасмур": 6, "хмарь": 6, "хмар": 6,
    "переменная облачность": 7, "пер.облачность": 7, "перем": 7,
    "гроза": 8, "гроз": 8,
}

WEATHER_IDS = set(WEATHER_TYPES.keys())


def normalize_antenna_code(s: str) -> str:
    """Е (кириллица) → E (латиница), убрать пробелы, привести к верхнему регистру."""
    s = s.upper()
    s = s.replace("Е", "E").replace("С", "C")  # кириллица → латиница
    s = re.sub(r"\s+", "", s)
    return s


def parse_note_for_antennas(note: str, day_date: date):
    """
    Парсит текст примечания, находит все антенны.
    Ищет любые коды вида [WESNC]NNNN (3-4 цифры).
    """
    if not note or not isinstance(note, str):
        return []

    # Нормализация кодов: Е(кир)+цифры -> E(лат)+цифры, убрать пробелы/дефисы
    normalized = note.upper()
    # "Е-1855", "Е 1855", "Е1855" -> "E1855"
    normalized = re.sub(r"Е[-\s]*(\d{3,4})", r"E\1", normalized)
    normalized = re.sub(r"С[-\s]*(\d{3,4})", r"C\1", normalized)
    # "E- 1840" -> "E1840", "W - 1816" -> "W1816", "W-1816" -> "W1816"
    normalized = re.sub(r"([WESNC])[-\s]+(\d{3,4})", r"\1\2", normalized)

    # Ищем ЛЮБЫЕ коды [WESNC]1234
    found = []
    for m in re.finditer(r"([WESNC])(\d{3,4})", normalized):
        found.append((m.start(), m.end(), m.group(1) + m.group(2)))

    if not found:
        return []

    found.sort(key=lambda x: x[0])

    filtered = []
    for s, e, code in found:
        if filtered and s < filtered[-1][1]:
            continue
        filtered.append((s, e, code))

    result = []
    for i, (s, e, code) in enumerate(filtered):
        next_start = filtered[i + 1][0] if i + 1 < len(filtered) else len(normalized)
        description = normalized[e:next_start].strip(" ;,.")
        result.append((code, description))

    return result

def parse_temperature(val):
    """'-16С' → -16.0, '15' → 15.0, '' → None"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s:
        return None
    # Убираем 'С', 'C', '°', пробелы
    s = re.sub(r"[СC°с\s]", "", s)
    # Заменяем запятую на точку
    s = s.replace(",", ".")
    # Ищем число (может быть со знаком)
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group())
    except ValueError:
        return None


def parse_time(val):
    """'01 00' → '01:00', '9:30' → '09:30', '' → None"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s:
        return None
    # '01 00' → '01:00'
    m = re.match(r"^(\d{1,2})\s+(\d{2})$", s)
    if m:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    # '9:30' → '09:30'
    m = re.match(r"^(\d{1,2}):(\d{2})$", s)
    if m:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    return s  # как есть


def map_weather(val):
    """Погода из Excel → weather_type_id (1-8) или None."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip().lower()
    if not s:
        return None
    # Прямое совпадение
    if s in WEATHER_MAP:
        return WEATHER_MAP[s]
    # Частичное — ищем первое вхождение
    for key, wid in WEATHER_MAP.items():
        if key in s:
            return wid
    # Если не нашли — None
    return None


def parse_date(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.date()
    if isinstance(val, date):
        return val
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None


# ============ ИМПОРТ КНИГИ 1 ============

def import_errors_book(path: str):
    print(f"\n=== Импорт {path} (журнал ошибок антенн) ===")
    df = pd.read_excel(path, header=0)

    db = JournalSessionLocal()
    created_days = 0
    created_entries = 0
    skipped = 0

    try:
        for idx, row in df.iterrows():
            d = parse_date(row.get("Дата"))
            grid_raw = row.get("Решетка", "")
            grid_name = normalize_grid_name(grid_raw)
            note = row.get("Примечание")

            if d is None:
                skipped += 1
                continue

            grid_id = GRID_NAME_TO_ID.get(grid_name)
            if grid_id is None:
                print(f"  [{idx}] неизвестный диапазон: {grid_name!r} — пропускаю")
                skipped += 1
                continue

            note_str = str(note) if note is not None and not (isinstance(note, float) and pd.isna(note)) else ""

            day = ErrorLogDay(
                date=d,
                grid_id=grid_id,
                version=1,
                is_active=True,
                is_ok=True,
            )
            db.add(day)
            db.flush()
            created_days += 1

            antennas = parse_note_for_antennas(note_str, d)
            if antennas:
                for code, desc in antennas:
                    events = [
                        {"id": "ev-import-bd", "type": "breakdown",
                         "date": str(d), "time": None, "date_end": None,
                         "time_end": None, "note": desc or ""},
                        {"id": "ev-import-rs", "type": "restore",
                         "date": str(d), "time": "23:59", "date_end": None,
                         "time_end": None, "note": "autoclose on import"},
                    ]
                    entry = ErrorLogEntry(
                        error_log_day_id=day.id,
                        antenna_code=code,
                        error_description=desc or None,
                        is_ok=True,
                        broken_since=str(d),
                        broken_until=str(d),
                        events_json=json.dumps(events, ensure_ascii=False),
                    )
                    db.add(entry)
                    created_entries += 1

            else:
                # одна запись MULTI (тоже автозакрытие)
                events = [
                    {"id": "ev-import-bd", "type": "breakdown",
                     "date": str(d), "time": None, "date_end": None,
                     "time_end": None, "note": note_str or ""},
                    {"id": "ev-import-rs", "type": "restore",
                     "date": str(d), "time": "23:59", "date_end": None,
                     "time_end": None, "note": "autoclose on import"},
                ]
                entry = ErrorLogEntry(
                    error_log_day_id=day.id,
                    antenna_code="MULTI",
                    error_description=note_str or None,
                    is_ok=True,
                    broken_since=str(d),
                    broken_until=str(d),
                    events_json=json.dumps(events, ensure_ascii=False),
                )
                db.add(entry)
                created_entries += 1

            if (idx + 1) % 100 == 0:
                db.commit()
                print(f"  ... {idx + 1} строк обработано")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"ОШИБКА: {e}")
        raise
    finally:
        db.close()

    print(f"Создано дней: {created_days}, записей: {created_entries}, пропущено: {skipped}")


# ============ ИМПОРТ КНИГИ 2 ============

def import_observations_book(path: str):
    print(f"\n=== Импорт {path} (журнал наблюдений) ===")
    df = pd.read_excel(path, header=None)

    # Пропускаем 3 строки шапки (0, 1, 2)
    data = df.iloc[3:]

    db = JournalSessionLocal()
    created_days = 0
    created_weather = 0
    created_equipment = 0
    skipped = 0

    try:
        for idx, row in data.iterrows():
            d = parse_date(row.iloc[0])
            if d is None:
                skipped += 1
                continue

            duty = row.iloc[44] if len(row) > 46 else None
            duty_str = str(duty).strip() if duty is not None and not (isinstance(duty, float) and pd.isna(duty)) else None
            if duty_str == "" or duty_str == "nan":
                duty_str = None

            obs = ObservationDay(
                date=d,
                version=1,
                is_active=True,
                duty_custom=duty_str,
            )
            db.add(obs)
            db.flush()
            created_days += 1

            # Погода: часы 0-11 (столбцы 1,3,5,...,23 — температура; 2,4,...,24 — погода)
            for hour in range(11):
                temp_col = 1 + hour * 2
                weather_col = 2 + hour * 2
                if len(row) <= weather_col:
                    continue
                temp = parse_temperature(row.iloc[temp_col])
                weather_id = map_weather(row.iloc[weather_col])
                if temp is not None or weather_id is not None:
                    db.add(HourlyWeather(
                        observation_day_id=obs.id,
                        hour=hour,
                        temperature=temp,
                        weather_type_id=weather_id,
                    ))
                    created_weather += 1

            # Оборудование
            for start_col, name, range_id in EQUIPMENT_RANGES:
                if range_id is None:
                    continue
                if len(row) <= start_col + 2:
                    continue
                t_start = parse_time(row.iloc[start_col])
                t_stop = parse_time(row.iloc[start_col + 1])
                note_val = row.iloc[start_col + 2]
                note = str(note_val).strip() if note_val is not None and not (isinstance(note_val, float) and pd.isna(note_val)) else None
                if note == "" or note == "nan":
                    note = None
                if t_start or t_stop or note:
                    db.add(EquipmentLog(
                        observation_day_id=obs.id,
                        equipment_range_id=range_id,
                        time_start=t_start,
                        time_stop=t_stop,
                        note=note,
                    ))
                    created_equipment += 1

            if (created_days) % 100 == 0:
                db.commit()
                print(f"  ... {created_days} дней обработано")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"ОШИБКА: {e}")
        raise
    finally:
        db.close()

    print(f"Создано дней: {created_days}, погоды: {created_weather}, оборудования: {created_equipment}, пропущено: {skipped}")


# ============ MAIN ============

def main():
    base = Path("/app/migration")
    book1 = base / "Книга1.xlsx"
    book2 = base / "Книга2.xlsx"

    if not book1.exists() or not book2.exists():
        print(f"Не найдены файлы в {base}: book1={book1.exists()}, book2={book2.exists()}")
        sys.exit(1)

    print("Создаю таблицы (если ещё нет)...")
    JournalBase.metadata.create_all(bind=journal_engine)

    import_errors_book(str(book1))
    import_observations_book(str(book2))

    print("\n=== ГОТОВО ===")


if __name__ == "__main__":
    main()
