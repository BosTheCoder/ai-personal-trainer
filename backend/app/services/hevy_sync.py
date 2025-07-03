"""Hevy synchronization service for pushing workouts to Hevy app."""

from typing import Any, Dict, Optional

from ..clients.hevy_client import HevyClient
from ..db import get_workout


async def push_workout_to_hevy(workout_id: str) -> str:
    """
    Push a local workout to Hevy as a routine.
    
    Args:
        workout_id: ID of the workout to push to Hevy
        
    Returns:
        The routine ID returned by Hevy API
        
    Raises:
        ValueError: If workout is not found
        Exception: If Hevy API call fails
    """
    workout = get_workout(workout_id)
    if not workout:
        raise ValueError(f"Workout with ID {workout_id} not found")
    
    routine_data = _map_workout_to_hevy_routine(workout)
    
    hevy_client = HevyClient()
    response = await hevy_client.post_routine(routine_data)
    
    routine_id = response.get("id")
    if not routine_id:
        raise Exception("Hevy API response missing routine ID")
    
    return routine_id


def _map_workout_to_hevy_routine(workout) -> Dict[str, Any]:
    """
    Map a local Workout object to Hevy routine payload format.
    
    Args:
        workout: Workout object from database
        
    Returns:
        Dictionary in Hevy routine format
    """
    hevy_exercises = []
    for exercise in workout.exercises:
        hevy_exercise = {
            "name": exercise.get("name", "Unknown Exercise"),
            "sets": []
        }
        
        if "sets" in exercise:
            if isinstance(exercise["sets"], list):
                hevy_exercise["sets"] = exercise["sets"]
            else:
                sets_count = exercise["sets"]
                reps = exercise.get("reps", 1)
                weight = exercise.get("weight", 0)
                
                for _ in range(sets_count):
                    set_data = {"reps": reps}
                    if weight > 0:
                        set_data["weight"] = weight
                    hevy_exercise["sets"].append(set_data)
        
        if "notes" in exercise:
            hevy_exercise["notes"] = exercise["notes"]
            
        hevy_exercises.append(hevy_exercise)
    
    routine_payload = {
        "title": f"Workout from {workout.date.strftime('%Y-%m-%d %H:%M')}",
        "exercises": hevy_exercises,
        "notes": f"Imported workout from AI Personal Trainer on {workout.date.isoformat()}"
    }
    
    return routine_payload
