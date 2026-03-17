"""Verify all database tables have correct schema."""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "wifisense.db"

if not db_path.exists():
    print("❌ Database does not exist")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

print("Database Schema Verification")
print("=" * 60)

expected_tables = {
    "events": ["id", "timestamp", "event_type", "confidence", "provider", 
               "metadata_json", "zone_id", "is_false_positive", "user_notes"],
    "calibration_profiles": ["id", "name", "baseline_json", "created_at", 
                            "updated_at", "is_active"],
    "behavior_patterns": ["id", "hour_of_day", "day_of_week", 
                         "presence_probability", "avg_movement_level", 
                         "sample_count", "last_updated"],
    "zones": ["id", "name", "rssi_min", "rssi_max", "alert_config_json", 
              "created_at"],
    "performance_metrics": ["id", "timestamp", "capture_time_ms", 
                           "processing_time_ms", "detection_time_ms", 
                           "total_latency_ms", "memory_usage_mb", 
                           "cpu_usage_percent"]
}

all_ok = True

for table_name, expected_columns in expected_tables.items():
    print(f"\n{table_name}:")
    
    if table_name not in tables:
        print(f"  ❌ Table does not exist")
        all_ok = False
        continue
    
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    
    missing = set(expected_columns) - set(columns)
    extra = set(columns) - set(expected_columns)
    
    if not missing and not extra:
        print(f"  ✓ All columns present ({len(columns)} columns)")
    else:
        if missing:
            print(f"  ❌ Missing columns: {missing}")
            all_ok = False
        if extra:
            print(f"  ⚠ Extra columns: {extra}")
    
    # Show all columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = cursor.fetchall()
    for col in cols:
        print(f"    - {col[1]} ({col[2]})")

# Check indexes
print("\n" + "=" * 60)
print("Indexes:")
cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
indexes = cursor.fetchall()
for idx_name, tbl_name in indexes:
    if not idx_name.startswith("sqlite_"):
        print(f"  ✓ {idx_name} on {tbl_name}")

conn.close()

print("\n" + "=" * 60)
if all_ok:
    print("✓ All tables and columns verified successfully!")
else:
    print("❌ Some issues found in schema")
