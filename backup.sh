#!/bin/bash
# Скрипт резервного копирования базы данных
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
cp journal.db "$BACKUP_DIR/journal_$DATE.db"
echo "Бэкап создан: $BACKUP_DIR/journal_$DATE.db"

# Оставляем только последние 7 копий
ls -t "$BACKUP_DIR"/journal_*.db | tail -n +8 | xargs -r rm
echo "Старые бэкапы удалены (оставлено 7 последних)"
