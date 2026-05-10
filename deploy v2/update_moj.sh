#!/bin/bash
# update_moj.sh — Download latest MoJ CSV and update the database
# Schedule: crontab -e → 0 6 * * 0 /path/to/update_moj.sh
#
# Usage: ./update_moj.sh [directory]

DIR="${1:-/home/claude}"
CSV="$DIR/moj_weekly.csv"
LOG="$DIR/moj_update.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') — Starting MoJ update" >> "$LOG"

# Download
curl -s --max-time 30 -o "$CSV.new" \
  "https://www.data.gov.qa/api/explore/v2.1/catalog/datasets/weekly-real-estates-sales-bulletin/exports/csv?lang=ar&timezone=Asia/Qatar&use_labels=true&delimiter=,"

if [ $? -ne 0 ] || [ ! -s "$CSV.new" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Download FAILED" >> "$LOG"
    rm -f "$CSV.new"
    exit 1
fi

NEW_SIZE=$(wc -c < "$CSV.new")
echo "$(date '+%Y-%m-%d %H:%M:%S') — Downloaded $NEW_SIZE bytes" >> "$LOG"

# Replace
mv "$CSV.new" "$CSV"

# Update DB
cd "$DIR"
python3 moj_db.py update "$CSV" >> "$LOG" 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') — Done" >> "$LOG"
