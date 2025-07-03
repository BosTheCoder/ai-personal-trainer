"""Hevy synchronization service that combines pull and push operations."""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict

scripts_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts")
sys.path.insert(0, scripts_path)

backend_path = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, backend_path)

from ..clients.hevy_client import HevyClient  # noqa: E402
from ..db import (  # noqa: E402
    create_workout,
    get_recent_workouts,
    get_workout,
    update_workout,
)
from ..models import Workout  # noqa: E402
from ..services.hevy_sync import push_workout_to_hevy  # noqa: E402

logger = logging.getLogger(__name__)


class SyncService:
    """Service for managing Hevy synchronization operations."""

    def __init__(self):
        self.is_running = False
        self.last_sync_time = None
        self.sync_interval = int(os.getenv("HEVY_SYNC_INTERVAL_HOURS", "6")) * 3600

    async def run_sync(self) -> Dict[str, Any]:
        """
        Run a complete sync operation (pull from Hevy + push to Hevy).

        Returns:
            Dictionary with sync results and timing information
        """
        start_time = datetime.now()
        logger.info(f"Starting Hevy sync at {start_time.isoformat()}")

        result = {
            "start_time": start_time.isoformat(),
            "pull_success": False,
            "push_success": False,
            "pull_error": None,
            "push_error": None,
            "end_time": None,
            "duration_seconds": None,
        }

        try:
            logger.info("Starting Hevy pull operation...")
            await self._run_pull_operation()
            result["pull_success"] = True
            logger.info("Hevy pull operation completed successfully")

        except Exception as e:
            result["pull_error"] = str(e)
            logger.error(f"Hevy pull operation failed: {e}")

        try:
            logger.info("Starting Hevy push operation...")
            recent_workouts = get_recent_workouts(days=7)
            push_count = 0

            for workout in recent_workouts:
                try:
                    await push_workout_to_hevy(workout.id)
                    push_count += 1
                except Exception as e:
                    logger.warning(f"Failed to push workout {workout.id}: {e}")

            result["push_success"] = True
            result["pushed_workouts"] = push_count
            logger.info(
                f"Hevy push operation completed successfully. "
                f"Pushed {push_count} workouts"
            )

        except Exception as e:
            result["push_error"] = str(e)
            logger.error(f"Hevy push operation failed: {e}")

        end_time = datetime.now()
        result["end_time"] = end_time.isoformat()
        result["duration_seconds"] = (end_time - start_time).total_seconds()

        self.last_sync_time = end_time
        logger.info(
            f"Hevy sync completed at {end_time.isoformat()} "
            f"(duration: {result['duration_seconds']:.2f}s)"
        )

        return result

    async def _run_pull_operation(self):
        """Run the Hevy pull operation (equivalent to pull_hevy.main())."""
        from datetime import datetime, timedelta, timezone

        client = HevyClient()
        logger.info("Hevy client initialized successfully")

        logger.info("Fetching workouts from last 30 days...")
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
                    workout_date = datetime.fromisoformat(
                        workout["created_at"].replace("Z", "+00:00")
                    )
                    if workout_date >= thirty_days_ago:
                        filtered_workouts.append(workout)
                    else:
                        all_workouts.extend(filtered_workouts)
                        break

                all_workouts.extend(filtered_workouts)

                if len(workouts) < page_size:
                    break

                page += 1

            except Exception as e:
                logger.error(f"Error fetching workouts page {page}: {e}")
                break

        logger.info(f"Fetched {len(all_workouts)} workouts from Hevy API")

        new_count = 0
        updated_count = 0
        error_count = 0

        for hevy_workout in all_workouts:
            try:
                local_workout = self._transform_hevy_workout_to_local(hevy_workout)
                is_new, operation = self._upsert_workout(local_workout)

                if operation == "created":
                    new_count += 1
                elif operation == "updated":
                    updated_count += 1
                else:
                    error_count += 1
                    logger.warning(
                        f"Failed to upsert workout {local_workout.id}: {operation}"
                    )

            except Exception as e:
                error_count += 1
                logger.error(f"Error processing workout: {e}")

        logger.info(
            f"Pull sync completed: {new_count} new workouts, "
            f"{updated_count} updated workouts, {error_count} errors"
        )

    def _transform_hevy_workout_to_local(self, hevy_workout: Dict) -> Workout:
        """Transform Hevy API workout format to local Workout model."""
        workout_date = datetime.fromisoformat(
            hevy_workout["created_at"].replace("Z", "+00:00")
        )

        exercises = []
        for exercise in hevy_workout.get("exercises", []):
            exercises.append(
                {
                    "name": exercise.get("exercise_template", {}).get(
                        "name", "Unknown"
                    ),
                    "sets": exercise.get("sets", []),
                    "notes": exercise.get("notes", ""),
                }
            )

        return Workout(id=hevy_workout["id"], date=workout_date, exercises=exercises)

    def _upsert_workout(self, workout: Workout):
        """Upsert workout into database."""
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

    async def start_background_sync(self):
        """Start the background sync task that runs every sync_interval seconds."""
        logger.info(
            f"Starting background Hevy sync task "
            f"(interval: {self.sync_interval/3600:.1f} hours)"
        )

        while True:
            try:
                await self.run_sync()
            except Exception as e:
                logger.error(f"Background sync failed: {e}")

            await asyncio.sleep(self.sync_interval)


sync_service = SyncService()
