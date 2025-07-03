import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.clients.hevy_client import HevyClient
from app.db import create_workout, get_workout, update_workout
from app.models import Workout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def transform_hevy_workout_to_local(hevy_workout: Dict) -> Workout:
    """Transform Hevy API workout format to local Workout model."""
    workout_date = datetime.fromisoformat(hevy_workout["created_at"].replace("Z", "+00:00"))
    
    exercises = []
    for exercise in hevy_workout.get("exercises", []):
        exercises.append({
            "name": exercise.get("exercise_template", {}).get("name", "Unknown"),
            "sets": exercise.get("sets", []),
            "notes": exercise.get("notes", "")
        })
    
    return Workout(
        id=hevy_workout["id"],
        date=workout_date,
        exercises=exercises
    )


async def fetch_workouts_last_30_days(client: HevyClient) -> List[Dict]:
    """Fetch all workouts from last 30 days, handling pagination."""
    from datetime import timezone
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    all_workouts = []
    page = 1
    page_size = 50
    
    while True:
        try:
            response = await client.get_workouts(page=page, page_size=page_size)
            workouts = response.get("workouts", [])
            
            if not workouts:
                break
                
            filtered_workouts = []
            for workout in workouts:
                workout_date = datetime.fromisoformat(workout["created_at"].replace("Z", "+00:00"))
                if workout_date >= thirty_days_ago:
                    filtered_workouts.append(workout)
                else:
                    return all_workouts + filtered_workouts
            
            all_workouts.extend(filtered_workouts)
            
            if len(workouts) < page_size:
                break
                
            page += 1
            
        except Exception as e:
            logger.error(f"Error fetching workouts page {page}: {e}")
            break
    
    return all_workouts


def upsert_workout(workout: Workout) -> Tuple[bool, str]:
    """
    Upsert workout into database.
    Returns (is_new, operation_type) where is_new indicates if it was created vs updated.
    """
    try:
        existing_workout = get_workout(workout.id)
        
        if existing_workout:
            success = update_workout(workout.id, workout)
            if success:
                return False, "updated"
            else:
                return False, "update_failed"
        else:
            created_id = create_workout(workout)
            if created_id:
                return True, "created"
            else:
                return False, "create_failed"
                
    except Exception as e:
        logger.error(f"Error upserting workout {workout.id}: {e}")
        return False, "error"


async def main():
    """Main function to pull and sync Hevy workouts."""
    logger.info("Starting Hevy workout sync...")
    
    try:
        client = HevyClient()
        logger.info("Hevy client initialized successfully")
        
        logger.info("Fetching workouts from last 30 days...")
        hevy_workouts = await fetch_workouts_last_30_days(client)
        logger.info(f"Fetched {len(hevy_workouts)} workouts from Hevy API")
        
        new_count = 0
        updated_count = 0
        error_count = 0
        
        for hevy_workout in hevy_workouts:
            try:
                local_workout = transform_hevy_workout_to_local(hevy_workout)
                is_new, operation = upsert_workout(local_workout)
                
                if operation == "created":
                    new_count += 1
                elif operation == "updated":
                    updated_count += 1
                else:
                    error_count += 1
                    logger.warning(f"Failed to upsert workout {local_workout.id}: {operation}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing workout: {e}")
        
        logger.info(f"Sync completed: {new_count} new workouts, {updated_count} updated workouts, {error_count} errors")
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
