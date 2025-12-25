#!/bin/bash
# Backup script for Be Thoughtful database

# Create backups directory if it doesn't exist
mkdir -p backups

# Get current timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Database file
DB_FILE="instance/database.db"

# Check if database exists
if [ ! -f "$DB_FILE" ]; then
    echo "Error: Database file not found at $DB_FILE"
    exit 1
fi

# Create backup
BACKUP_FILE="backups/database_${TIMESTAMP}.db"
cp "$DB_FILE" "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✓ Backup created successfully: $BACKUP_FILE"

    # Show backup size
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "  Size: $SIZE"

    # Count total backups
    BACKUP_COUNT=$(ls -1 backups/*.db 2>/dev/null | wc -l)
    echo "  Total backups: $BACKUP_COUNT"
else
    echo "✗ Backup failed!"
    exit 1
fi
