"""
Migration: Add calibration, behavior patterns, zones, and performance metrics models.

This migration adds the following tables:
- calibration_profiles: Store calibration baselines
- behavior_patterns: Store learned behavior patterns
- zones: Store monitoring zones
- performance_metrics: Store system performance metrics

It also adds new columns to the events table:
- zone_id: Link to zone
- is_false_positive: Flag for false positive events
- user_notes: User notes for events
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.database import engine


async def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    result = await conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = :table_name AND column_name = :column_name
    """), {"table_name": table_name, "column_name": column_name})
    return result.fetchone() is not None


async def table_exists(conn, table_name: str) -> bool:
    """Check if a table exists."""
    result = await conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = :table_name
    """), {"table_name": table_name})
    return result.fetchone() is not None


async def upgrade():
    """Apply migration."""
    async with engine.begin() as conn:
        print("Checking existing schema...")
        
        # Add new columns to events table if they don't exist
        if not await column_exists(conn, "events", "zone_id"):
            print("  Adding zone_id column to events table...")
            await conn.execute(text("ALTER TABLE events ADD COLUMN zone_id INTEGER"))
        else:
            print("  zone_id column already exists")
        
        if not await column_exists(conn, "events", "is_false_positive"):
            print("  Adding is_false_positive column to events table...")
            await conn.execute(text("ALTER TABLE events ADD COLUMN is_false_positive BOOLEAN DEFAULT 0"))
        else:
            print("  is_false_positive column already exists")
        
        if not await column_exists(conn, "events", "user_notes"):
            print("  Adding user_notes column to events table...")
            await conn.execute(text("ALTER TABLE events ADD COLUMN user_notes TEXT"))
        else:
            print("  user_notes column already exists")
        
        # Create calibration_profiles table if it doesn't exist
        if not await table_exists(conn, "calibration_profiles"):
            print("  Creating calibration_profiles table...")
            await conn.execute(text("""
                CREATE TABLE calibration_profiles (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    baseline_json TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP,
                    is_active BOOLEAN NOT NULL DEFAULT FALSE
                )
            """))
            
            await conn.execute(text("""
                CREATE INDEX ix_calibration_profiles_name ON calibration_profiles (name)
            """))
        else:
            print("  calibration_profiles table already exists")
        
        # Create behavior_patterns table if it doesn't exist
        if not await table_exists(conn, "behavior_patterns"):
            print("  Creating behavior_patterns table...")
            await conn.execute(text("""
                CREATE TABLE behavior_patterns (
                    id SERIAL PRIMARY KEY,
                    hour_of_day INTEGER NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    presence_probability FLOAT NOT NULL,
                    avg_movement_level FLOAT NOT NULL,
                    sample_count INTEGER NOT NULL,
                    last_updated TIMESTAMP NOT NULL
                )
            """))
            
            await conn.execute(text("""
                CREATE INDEX idx_hour_day ON behavior_patterns (hour_of_day, day_of_week)
            """))
        else:
            print("  behavior_patterns table already exists")
        
        # Create zones table if it doesn't exist
        if not await table_exists(conn, "zones"):
            print("  Creating zones table...")
            await conn.execute(text("""
                CREATE TABLE zones (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    rssi_min FLOAT NOT NULL,
                    rssi_max FLOAT NOT NULL,
                    alert_config_json TEXT NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP NOT NULL
                )
            """))
        else:
            print("  zones table already exists")
        
        # Create performance_metrics table if it doesn't exist
        if not await table_exists(conn, "performance_metrics"):
            print("  Creating performance_metrics table...")
            await conn.execute(text("""
                CREATE TABLE performance_metrics (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    capture_time_ms FLOAT NOT NULL,
                    processing_time_ms FLOAT NOT NULL,
                    detection_time_ms FLOAT NOT NULL,
                    total_latency_ms FLOAT NOT NULL,
                    memory_usage_mb FLOAT NOT NULL,
                    cpu_usage_percent FLOAT NOT NULL
                )
            """))
            
            await conn.execute(text("""
                CREATE INDEX ix_performance_metrics_timestamp ON performance_metrics (timestamp)
            """))
        else:
            print("  performance_metrics table already exists")
        
        print("✓ Migration 001 applied successfully")


async def downgrade():
    """Rollback migration."""
    async with engine.begin() as conn:
        # Drop new tables
        await conn.execute(text("DROP TABLE IF EXISTS performance_metrics"))
        await conn.execute(text("DROP TABLE IF EXISTS zones"))
        await conn.execute(text("DROP TABLE IF EXISTS behavior_patterns"))
        await conn.execute(text("DROP TABLE IF EXISTS calibration_profiles"))
        
        # Note: SQLite doesn't support DROP COLUMN directly
        # To remove columns from events table, we would need to:
        # 1. Create new table without those columns
        # 2. Copy data
        # 3. Drop old table
        # 4. Rename new table
        # For simplicity, we'll leave the columns in place during downgrade
        
        print("✓ Migration 001 rolled back successfully")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python 001_add_calibration_models.py [upgrade|downgrade]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "upgrade":
        asyncio.run(upgrade())
    elif command == "downgrade":
        asyncio.run(downgrade())
    else:
        print(f"Unknown command: {command}")
        print("Usage: python 001_add_calibration_models.py [upgrade|downgrade]")
        sys.exit(1)
