"""
Migration 003: Add notification_logs table

This migration creates the notification_logs table to persist logs of sent notifications.
Supports PostgreSQL and SQLite.

Fields:
- id: Primary key
- timestamp: Date/time of sending (indexed)
- channel: Channel used (telegram, whatsapp, webhook) (indexed)
- event_type: Type of event that generated the notification
- confidence: Detection confidence
- recipient: Recipient (chat_id, phone, url)
- success: Whether sending was successful
- error_message: Error message (if any)
- alert_data: Complete alert data in JSON
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.database import engine


async def table_exists(conn, table_name: str) -> bool:
    """Check if a table exists."""
    result = await conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = :table_name
    """), {"table_name": table_name})
    return result.fetchone() is not None


async def upgrade():
    """Apply migration - create notification_logs table."""
    async with engine.begin() as conn:
        print("Checking existing schema...")
        
        # Create notification_logs table if it doesn't exist
        if not await table_exists(conn, "notification_logs"):
            print("  Creating notification_logs table...")
            await conn.execute(text("""
                CREATE TABLE notification_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    channel VARCHAR(50) NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    confidence FLOAT NOT NULL,
                    recipient VARCHAR(200) NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    alert_data TEXT NOT NULL DEFAULT '{}'
                )
            """))
            
            # Create indexes
            await conn.execute(text("""
                CREATE INDEX ix_notification_logs_timestamp ON notification_logs (timestamp)
            """))
            
            await conn.execute(text("""
                CREATE INDEX ix_notification_logs_channel ON notification_logs (channel)
            """))
            
            print("  ✓ notification_logs table created successfully")
        else:
            print("  notification_logs table already exists")
        
        print("✓ Migration 003 applied successfully")


async def downgrade():
    """Rollback migration - drop notification_logs table."""
    async with engine.begin() as conn:
        print("Rolling back migration 003...")
        await conn.execute(text("DROP TABLE IF EXISTS notification_logs"))
        print("✓ Migration 003 rolled back successfully")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python 003_add_notification_logs.py [upgrade|downgrade]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "upgrade":
        asyncio.run(upgrade())
    elif command == "downgrade":
        asyncio.run(downgrade())
    else:
        print(f"Unknown command: {command}")
        print("Usage: python 003_add_notification_logs.py [upgrade|downgrade]")
        sys.exit(1)
