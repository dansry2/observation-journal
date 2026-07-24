#!/bin/bash
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y-%m-%d_%H-%M-%S)

# Дамп journal.db в SQL
sqlite3 journal.db .dump > "$BACKUP_DIR/journal_$DATE.sql"
echo "Бэкап создан: $BACKUP_DIR/journal_$DATE.sql"

# Оставляем только последние 7 копий
ls -t "$BACKUP_DIR"/journal_*.sql | tail -n +8 | xargs -r rm
echo "Старые бэкапы удалены (оставлено 7 последних)"
