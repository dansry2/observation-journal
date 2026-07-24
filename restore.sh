#!/bin/bash
BACKUP_DIR="./backups"

echo "Доступные бэкапы:"
ls -1t "$BACKUP_DIR"/journal_*.sql 2>/dev/null | head -10

echo ""
echo "Введите имя файла для восстановления:"
read -r BACKUP_FILE

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Файл не найден!"
    exit 1
fi

# Останавливаем сервер
pkill -f uvicorn 2>/dev/null
sleep 1

# Сохраняем текущую базу
cp journal.db "journal_before_restore_$(date +%Y%m%d_%H%M%S).db" 2>/dev/null

# Удаляем старую и создаём новую из SQL-дампа
rm -f journal.db
sqlite3 journal.db < "$BACKUP_FILE"

echo "База восстановлена из: $BACKUP_FILE"
echo "Предыдущая база сохранена как journal_before_restore_*.db"
