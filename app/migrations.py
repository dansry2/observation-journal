from sqlalchemy import inspect, text


REQUIRED_COLUMNS = {
    "error_log_entries": {
        "start_time": "VARCHAR",
        "end_time": "VARCHAR",
        "broken_since": "VARCHAR",
        "broken_until": "VARCHAR",
        "events_json": "TEXT",
    },
}


def migrate_columns(engine):
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"[migration] Проверка таблиц: {existing_tables}")

    with engine.connect() as conn:
        for table_name, columns in REQUIRED_COLUMNS.items():
            if table_name not in existing_tables:
                continue
            existing_columns = {c["name"] for c in inspector.get_columns(table_name)}
            for col_name, col_type in columns.items():
                if col_name not in existing_columns:
                    try:
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                        print(f"[migration] Добавлена колонка {table_name}.{col_name}")
                    except Exception as e:
                        print(f"[migration] Ошибка добавления {table_name}.{col_name}: {e}")
