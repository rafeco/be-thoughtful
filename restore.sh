#!/bin/bash
# Restore script for Be Thoughtful database

DB_FILE="instance/database.db"
BACKUPS_DIR="backups"

# Check if backups directory exists
if [ ! -d "$BACKUPS_DIR" ]; then
    echo "Error: No backups directory found!"
    echo "Run ./backup.sh first to create a backup."
    exit 1
fi

# List available backups
echo "Available backups:"
echo ""

BACKUPS=($(ls -1t "$BACKUPS_DIR"/*.db 2>/dev/null))

if [ ${#BACKUPS[@]} -eq 0 ]; then
    echo "No backups found!"
    exit 1
fi

# Display backups with numbers
for i in "${!BACKUPS[@]}"; do
    BACKUP_FILE="${BACKUPS[$i]}"
    BASENAME=$(basename "$BACKUP_FILE")
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    TIMESTAMP=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$BACKUP_FILE")
    echo "  [$i] $BASENAME"
    echo "      Created: $TIMESTAMP"
    echo "      Size: $SIZE"
    echo ""
done

# Ask user to select a backup
echo -n "Enter backup number to restore (or 'q' to quit): "
read SELECTION

# Check if user wants to quit
if [ "$SELECTION" = "q" ] || [ "$SELECTION" = "Q" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Validate selection
if ! [[ "$SELECTION" =~ ^[0-9]+$ ]] || [ "$SELECTION" -lt 0 ] || [ "$SELECTION" -ge ${#BACKUPS[@]} ]; then
    echo "Error: Invalid selection!"
    exit 1
fi

SELECTED_BACKUP="${BACKUPS[$SELECTION]}"
echo ""
echo "Selected: $(basename "$SELECTED_BACKUP")"
echo ""

# Confirm restoration
echo "WARNING: This will overwrite the current database!"
echo -n "Are you sure you want to continue? (yes/no): "
read CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Create safety backup of current database before restoring
if [ -f "$DB_FILE" ]; then
    SAFETY_BACKUP="backups/database_before_restore_$(date +"%Y%m%d_%H%M%S").db"
    cp "$DB_FILE" "$SAFETY_BACKUP"
    echo "✓ Safety backup created: $SAFETY_BACKUP"
fi

# Restore the backup
cp "$SELECTED_BACKUP" "$DB_FILE"

if [ $? -eq 0 ]; then
    echo "✓ Database restored successfully!"
    echo ""
    echo "Restart the Flask server to use the restored database."
else
    echo "✗ Restore failed!"
    if [ -f "$SAFETY_BACKUP" ]; then
        echo "Your original database is backed up at: $SAFETY_BACKUP"
    fi
    exit 1
fi
