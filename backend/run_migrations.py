"""
Simple migration runner for WiFiSense database.

Usage:
    python run_migrations.py upgrade    # Apply all pending migrations
    python run_migrations.py downgrade  # Rollback last migration
    python run_migrations.py init       # Initialize database with all tables
"""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import init_db


async def init_database():
    """Initialize database with all tables from models."""
    print("Initializing database...")
    await init_db()
    print("✓ Database initialized successfully")


async def run_migration(migration_file: Path, command: str):
    """Run a specific migration file."""
    print(f"Running migration: {migration_file.name}")
    
    # Import and run the migration
    import importlib.util
    spec = importlib.util.spec_from_file_location("migration", migration_file)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    
    if command == "upgrade":
        await migration.upgrade()
    elif command == "downgrade":
        await migration.downgrade()


async def upgrade_all():
    """Apply all pending migrations."""
    migrations_dir = Path(__file__).parent / "migrations"
    
    if not migrations_dir.exists():
        print("No migrations directory found")
        return
    
    migration_files = sorted(migrations_dir.glob("*.py"))
    
    if not migration_files:
        print("No migration files found")
        return
    
    for migration_file in migration_files:
        if migration_file.name.startswith("__"):
            continue
        await run_migration(migration_file, "upgrade")


async def downgrade_last():
    """Rollback the last migration."""
    migrations_dir = Path(__file__).parent / "migrations"
    
    if not migrations_dir.exists():
        print("No migrations directory found")
        return
    
    migration_files = sorted(migrations_dir.glob("*.py"), reverse=True)
    
    if not migration_files:
        print("No migration files found")
        return
    
    # Get the first (most recent) migration
    for migration_file in migration_files:
        if migration_file.name.startswith("__"):
            continue
        await run_migration(migration_file, "downgrade")
        break


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        asyncio.run(init_database())
    elif command == "upgrade":
        asyncio.run(upgrade_all())
    elif command == "downgrade":
        asyncio.run(downgrade_last())
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
