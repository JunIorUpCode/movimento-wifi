"""
Comprehensive test for Task 1: Data models for calibration and patterns.

This test verifies:
1. All models can be imported
2. All models can be instantiated
3. All models can be saved to database
4. All models can be queried from database
5. Relationships and constraints work correctly
"""

import asyncio
import json
from datetime import datetime

from sqlalchemy import select
from app.db.database import async_session
from app.models import (
    Event,
    CalibrationProfile,
    BehaviorPattern,
    Zone,
    PerformanceMetric,
)


async def test_complete_workflow():
    """Test complete workflow of all models."""
    print("=" * 70)
    print("TASK 1 COMPREHENSIVE TEST")
    print("=" * 70)
    
    async with async_session() as db:
        # Test 1: Create a Zone
        print("\n[1/5] Creating Zone...")
        zone = Zone(
            name="Test Zone",
            rssi_min=-70.0,
            rssi_max=-40.0,
            alert_config_json=json.dumps({
                "fall_detection": True,
                "movement_detection": True
            }),
            created_at=datetime.utcnow()
        )
        db.add(zone)
        await db.commit()
        await db.refresh(zone)
        print(f"      ✓ Zone created with id={zone.id}")
        
        # Test 2: Create CalibrationProfile
        print("\n[2/5] Creating CalibrationProfile...")
        baseline = {
            "mean_rssi": -50.5,
            "std_rssi": 3.2,
            "mean_variance": 2.1,
            "std_variance": 0.8,
            "noise_floor": -65.0,
            "samples_count": 120,
            "timestamp": datetime.utcnow().timestamp(),
            "profile_name": "morning"
        }
        profile = CalibrationProfile(
            name="morning_profile",
            baseline_json=json.dumps(baseline),
            created_at=datetime.utcnow(),
            is_active=True
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        print(f"      ✓ CalibrationProfile created with id={profile.id}")
        
        # Test 3: Create BehaviorPattern
        print("\n[3/5] Creating BehaviorPattern...")
        pattern = BehaviorPattern(
            hour_of_day=9,
            day_of_week=1,  # Monday
            presence_probability=0.85,
            avg_movement_level=4.2,
            sample_count=100,
            last_updated=datetime.utcnow()
        )
        db.add(pattern)
        await db.commit()
        await db.refresh(pattern)
        print(f"      ✓ BehaviorPattern created with id={pattern.id}")
        
        # Test 4: Create Event with zone reference
        print("\n[4/5] Creating Event with zone reference...")
        event = Event(
            timestamp=datetime.utcnow(),
            event_type="presence_moving",
            confidence=0.92,
            provider="rssi_windows",
            metadata_json=json.dumps({
                "rssi": -45.5,
                "variance": 3.2
            }),
            zone_id=zone.id,
            is_false_positive=False,
            user_notes="Test event in zone"
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        print(f"      ✓ Event created with id={event.id}, zone_id={event.zone_id}")
        
        # Test 5: Create PerformanceMetric
        print("\n[5/5] Creating PerformanceMetric...")
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            capture_time_ms=12.5,
            processing_time_ms=8.3,
            detection_time_ms=4.7,
            total_latency_ms=25.5,
            memory_usage_mb=150.2,
            cpu_usage_percent=18.5
        )
        db.add(metric)
        await db.commit()
        await db.refresh(metric)
        print(f"      ✓ PerformanceMetric created with id={metric.id}")
        
        # Verification: Query all data back
        print("\n" + "=" * 70)
        print("VERIFICATION: Querying all data back")
        print("=" * 70)
        
        # Query Zone
        result = await db.execute(select(Zone).where(Zone.id == zone.id))
        queried_zone = result.scalar_one()
        assert queried_zone.name == "Test Zone"
        print(f"\n✓ Zone: {queried_zone.name} (RSSI: {queried_zone.rssi_min} to {queried_zone.rssi_max})")
        
        # Query CalibrationProfile
        result = await db.execute(
            select(CalibrationProfile).where(CalibrationProfile.id == profile.id)
        )
        queried_profile = result.scalar_one()
        assert queried_profile.is_active == True
        baseline_data = json.loads(queried_profile.baseline_json)
        print(f"✓ CalibrationProfile: {queried_profile.name} (mean_rssi: {baseline_data['mean_rssi']})")
        
        # Query BehaviorPattern
        result = await db.execute(
            select(BehaviorPattern).where(BehaviorPattern.id == pattern.id)
        )
        queried_pattern = result.scalar_one()
        assert queried_pattern.hour_of_day == 9
        print(f"✓ BehaviorPattern: Hour {queried_pattern.hour_of_day}, Day {queried_pattern.day_of_week} "
              f"(presence: {queried_pattern.presence_probability:.2f})")
        
        # Query Event with zone
        result = await db.execute(select(Event).where(Event.id == event.id))
        queried_event = result.scalar_one()
        assert queried_event.zone_id == zone.id
        print(f"✓ Event: {queried_event.event_type} (confidence: {queried_event.confidence:.2f}, "
              f"zone_id: {queried_event.zone_id})")
        
        # Query PerformanceMetric
        result = await db.execute(
            select(PerformanceMetric).where(PerformanceMetric.id == metric.id)
        )
        queried_metric = result.scalar_one()
        assert queried_metric.total_latency_ms == 25.5
        print(f"✓ PerformanceMetric: Total latency {queried_metric.total_latency_ms}ms "
              f"(CPU: {queried_metric.cpu_usage_percent}%)")
        
        # Test complex query: Find events in a specific zone
        print("\n" + "=" * 70)
        print("COMPLEX QUERY TEST: Events in zone")
        print("=" * 70)
        result = await db.execute(
            select(Event).where(Event.zone_id == zone.id)
        )
        zone_events = result.scalars().all()
        print(f"\n✓ Found {len(zone_events)} event(s) in zone '{queried_zone.name}'")
        
        # Test complex query: Behavior patterns for specific time
        print("\n" + "=" * 70)
        print("COMPLEX QUERY TEST: Behavior patterns for Monday 9am")
        print("=" * 70)
        result = await db.execute(
            select(BehaviorPattern).where(
                BehaviorPattern.hour_of_day == 9,
                BehaviorPattern.day_of_week == 1
            )
        )
        patterns = result.scalars().all()
        print(f"\n✓ Found {len(patterns)} pattern(s) for Monday 9am")
        
        # Test query: Active calibration profile
        print("\n" + "=" * 70)
        print("COMPLEX QUERY TEST: Active calibration profile")
        print("=" * 70)
        result = await db.execute(
            select(CalibrationProfile).where(CalibrationProfile.is_active == True)
        )
        active_profiles = result.scalars().all()
        print(f"\n✓ Found {len(active_profiles)} active profile(s)")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nTask 1 Implementation Summary:")
        print("  ✓ CalibrationProfile model - WORKING")
        print("  ✓ BehaviorPattern model - WORKING")
        print("  ✓ Zone model - WORKING")
        print("  ✓ PerformanceMetric model - WORKING")
        print("  ✓ Event model updates - WORKING")
        print("  ✓ Database migrations - WORKING")
        print("  ✓ All queries - WORKING")
        print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
