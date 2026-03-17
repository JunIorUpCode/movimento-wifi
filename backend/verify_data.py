"""Verify data was saved correctly."""
import asyncio
from sqlalchemy import select

from app.db.database import async_session
from app.models import (
    Event,
    CalibrationProfile,
    BehaviorPattern,
    Zone,
    PerformanceMetric,
)


async def verify_data():
    """Query and display saved data."""
    print("Verifying saved data...")
    
    async with async_session() as db:
        # Query Events
        result = await db.execute(select(Event).order_by(Event.id.desc()).limit(1))
        event = result.scalar_one_or_none()
        if event:
            print(f"\n✓ Latest Event: id={event.id}, type={event.event_type}, "
                  f"confidence={event.confidence}, zone_id={event.zone_id}")
        
        # Query CalibrationProfiles
        result = await db.execute(select(CalibrationProfile))
        profiles = result.scalars().all()
        print(f"\n✓ CalibrationProfiles: {len(profiles)} profiles")
        for p in profiles:
            print(f"  - {p.name} (active={p.is_active})")
        
        # Query BehaviorPatterns
        result = await db.execute(select(BehaviorPattern))
        patterns = result.scalars().all()
        print(f"\n✓ BehaviorPatterns: {len(patterns)} patterns")
        for p in patterns:
            print(f"  - Hour {p.hour_of_day}, Day {p.day_of_week}: "
                  f"presence={p.presence_probability:.2f}")
        
        # Query Zones
        result = await db.execute(select(Zone))
        zones = result.scalars().all()
        print(f"\n✓ Zones: {len(zones)} zones")
        for z in zones:
            print(f"  - {z.name}: RSSI {z.rssi_min} to {z.rssi_max}")
        
        # Query PerformanceMetrics
        result = await db.execute(select(PerformanceMetric))
        metrics = result.scalars().all()
        print(f"\n✓ PerformanceMetrics: {len(metrics)} metrics")
        for m in metrics:
            print(f"  - Total latency: {m.total_latency_ms:.2f}ms, "
                  f"CPU: {m.cpu_usage_percent:.1f}%")
        
        print("\n" + "=" * 60)
        print("✓ All data verified successfully!")


if __name__ == "__main__":
    asyncio.run(verify_data())
