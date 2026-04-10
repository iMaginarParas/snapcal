#!/bin/bash

# FitSnap AI — Database Restore Script
# Usage: ./restore_database.sh <path_to_backup_file>

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <path_to_backup_file>"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable is not set."
    exit 1
fi

echo "--- STARTING DATABASE RESTORE ---"
echo "Target: $DATABASE_URL"
echo "Source: $BACKUP_FILE"

# Warn user
read -p "WARNING: This will overwrite CURRENT data. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Restore cancelled."
    exit 1
fi

# Run pg_restore
# --clean: Drop database objects before recreating them
# --if-exists: Ignore errors for objects that don't exist
# --no-owner: Don't set ownership
pg_restore --clean --if-exists --no-owner --dbname="$DATABASE_URL" "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "--- RESTORE SUCCESSFUL ---"
else
    echo "--- RESTORE FAILED ---"
    exit 1
fi
