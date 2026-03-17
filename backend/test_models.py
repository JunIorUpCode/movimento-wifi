"""Test that all models can be instantiated and saved to database."""
import asyncio
from datetime import datetime
import json

from app.db.database import async_session
from app.models import (
    Event,
    CalibrationProfile,
    BehaviorPattern,
    Zone,
    PerformanceMetric,
)


async def test_models():
    """Test creating instances of all models."""
    print("Testing SQLAlchemy models...")
    
    async with async_session() as db:
        # Test Event model
        print("\n1. Testing Event model...")
        event = Event(
            timestamp=datetime.utcnow(),
            event_type="presence_moving",
            confidence=0.85,
            provider="rssi_windows",
            metadata_json=json.dumps({"test": "data"}),
            zone_id=1,
            is_false_positive=False,
            user_notes="Test event"
        )
        db.add(event)
        await db.commit()
        print(f"   ✓ Created Event with id={event.id}")
        
        # Test CalibrationProfile model
        print("\n2. Testing CalibrationProfile model...")
        baseline_data = {
            "mean_rssi": -45.5,
            "std_rssi": 2.3,
            "mean_variance": 1.2,
            "std_variance": 0.5,
            "noise_floor": -60.0,
            "samples_count": 100,
            "timestamp": datetime.utcnow().timestamp()
        }
        profile = CalibrationProfile(
            name="test_profile",
            baseline_json=json.dumps(baseline_data),
            created_at=datetime.utcnow(),
            is_active=True
        )
        db.add(profile)
        await db.commit()
        print(f"   ✓ Created CalibrationProfile with id={profile.id}")
        
        # Test BehaviorPattern model
        print("\n3. Testing BehaviorPattern model...")
        pattern = BehaviorPattern(
            hour_of_day=14,
            day_of_week=2,
            presence_probability=0.75,
            avg_movement_level=3.5,
            sample_count=50,
            last_updated=datetime.utcnow()
        )
        db.add(pattern)
        await db.commit()
        print(f"   ✓ Created BehaviorPattern with id={pattern.id}")
        
        # Test Zone model
        print("\n4. Testing Zone model...")
        zone = Zone(
            name="Living Room",
            rssi_min=-60.0,
            rssi_max=-30.0,
            alert_config_json=json.dumps({"enabled": True}),
            created_at=datetime.utcnow()
        )
        db.add(zone)
        await db.commit()
        print(f"   ✓ Created Zone with id={zone.id}")
        
        # Test PerformanceMetric model
        print("\n5. Testing PerformanceMetric model...")
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            capture_time_ms=10.5,
            processing_time_ms=5.2,
            detection_time_ms=3.1,
            total_latency_ms=18.8,
            memory_usage_mb=125.5,
            cpu_usage_percent=15.3
        )
        db.add(metric)
        await db.commit()
        print(f"   ✓ Created PerformanceMetric with id={metric.id}")
        
        print("\n" + "=" * 60)
        print("✓ All models tested successfully!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_models())
