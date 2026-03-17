# Database Migrations

This directory contains database migration scripts for the WiFiSense system.

## Overview

The WiFiSense system uses SQLite with SQLAlchemy ORM. Migrations are simple Python scripts that can be run to upgrade or downgrade the database schema.

## Running Migrations

### Using the migration runner (recommended)

```bash
# Initialize database with all tables from models
python run_migrations.py init

# Apply all pending migrations
python run_migrations.py upgrade

# Rollback the last migration
python run_migrations.py downgrade
```

### Running individual migrations

```bash
# Apply a specific migration
python migrations/001_add_calibration_models.py upgrade

# Rollback a specific migration
python migrations/001_add_calibration_models.py downgrade
```

## Available Migrations

### 001_add_calibration_models.py

Adds support for calibration, behavior patterns, zones, and performance metrics.

**New Tables:**
- `calibration_profiles`: Store calibration baselines for different environments
- `behavior_patterns`: Store learned behavior patterns by hour/day
- `zones`: Define monitoring zones with RSSI ranges
- `performance_metrics`: Track system performance metrics

**Modified Tables:**
- `events`: Added `zone_id`, `is_false_positive`, and `user_notes` columns

## Creating New Migrations

To create a new migration:

1. Create a new file in the `migrations/` directory with format: `NNN_description.py`
2. Implement `upgrade()` and `downgrade()` async functions
3. Use SQLAlchemy's `text()` for raw SQL or ORM operations
4. Test both upgrade and downgrade paths

Example template:

```python
import asyncio
from sqlalchemy import text
from app.db.database import engine

async def upgrade():
    async with engine.begin() as conn:
        # Your upgrade logic here
        pass

async def downgrade():
    async with engine.begin() as conn:
        # Your downgrade logic here
        pass

if __name__ == "__main__":
    import sys
    command = sys.argv[1] if len(sys.argv) > 1 else "upgrade"
    if command == "upgrade":
        asyncio.run(upgrade())
    elif command == "downgrade":
        asyncio.run(downgrade())
```

## Verification

After running migrations, verify the schema:

```bash
# Check database structure
python check_db.py

# Verify all tables and columns
python verify_schema.py

# Test models can be instantiated
python test_models.py

# Verify data can be queried
python verify_data.py
```

## Notes

- SQLite has limited ALTER TABLE support (cannot drop columns directly)
- Always backup your database before running migrations
- Test migrations on a copy of production data first
- Migrations are idempotent - they check if changes already exist before applying
