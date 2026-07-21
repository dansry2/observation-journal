#!/bin/bash
BACKUP_DIR="./backups"

echo "Доступные бэкапы:"
ls -1t "$BACKUP_DIR"/journal_*.db 2>/dev/null | head -10

echo ""
echo "Введите имя файла для восстановления:"
read -r BACKUP_FILE

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Файл не найден!"
    exit 1
fi

# Останавливаем сервер если запущен
pkill -f uvicorn 2>/dev/null
sleep 1

# Делаем бэкап текущей базы перед восстановлением
cp journal.db "journal_before_restore_$(date +%Y%m%d_%H%M%S).db" 2>/dev/null
cp users.db "users_before_restore_$(date +%Y%m%d_%H%M%S).db" 2>/dev/null

# Восстанавливаем
cp "$BACKUP_FILE" journal.db
echo "База восстановлена из: $BACKUP_FILE"
echo "Предыдущая база сохранена как journal_before_restore_*.db"
