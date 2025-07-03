import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field

from ..ai.openrouter import send_prompt
from ..models import Workout
from ..utils import match_exercise_template


class WorkoutConstraints(BaseModel):
    goals: List[str] = Field(default_factory=list, description="User's fitness goals")
    equipment: List[str] = Field(default_factory=list, description="Available equipment")
    duration: int = Field(default=30, description="Duration in minutes", ge=10, le=180)
    fitness_level: str = Field(default="beginner", description="User's fitness level")


class WorkoutOverrides(BaseModel):
    specific_exercises: Optional[List[str]] = Field(None, description="Specific exercises to include")
    avoid_exercises: Optional[List[str]] = Field(None, description="Exercises to avoid")
    focus_areas: Optional[List[str]] = Field(None, description="Body areas to focus on")


class GenerateWorkoutRequest(BaseModel):
    constraints: WorkoutConstraints
    overrides: Optional[WorkoutOverrides] = None
    user_id: str = Field(..., description="User ID for API key retrieval")


def _suggest_weight_for_exercise(exercise_name: str, fitness_level: str) -> Optional[Dict[str, Any]]:
    """Suggest weight for an exercise based on name and fitness level."""
    exercise_lower = exercise_name.lower()
    
    weight_suggestions = {
        "beginner": {
            "squat": {"weight": 20, "unit": "kg"},
            "deadlift": {"weight": 30, "unit": "kg"},
            "bench press": {"weight": 20, "unit": "kg"},
            "overhead press": {"weight": 15, "unit": "kg"},
            "barbell row": {"weight": 20, "unit": "kg"},
            "bicep curl": {"weight": 8, "unit": "kg"},
            "tricep extension": {"weight": 8, "unit": "kg"},
        },
        "intermediate": {
            "squat": {"weight": 40, "unit": "kg"},
            "deadlift": {"weight": 60, "unit": "kg"},
            "bench press": {"weight": 40, "unit": "kg"},
            "overhead press": {"weight": 30, "unit": "kg"},
            "barbell row": {"weight": 35, "unit": "kg"},
            "bicep curl": {"weight": 12, "unit": "kg"},
            "tricep extension": {"weight": 12, "unit": "kg"},
        },
        "advanced": {
            "squat": {"weight": 80, "unit": "kg"},
            "deadlift": {"weight": 120, "unit": "kg"},
            "bench press": {"weight": 80, "unit": "kg"},
            "overhead press": {"weight": 60, "unit": "kg"},
            "barbell row": {"weight": 70, "unit": "kg"},
            "bicep curl": {"weight": 20, "unit": "kg"},
            "tricep extension": {"weight": 20, "unit": "kg"},
        },
    }
    
    level_weights = weight_suggestions.get(fitness_level.lower(), weight_suggestions["beginner"])
    
    for exercise_key, weight_info in level_weights.items():
        if exercise_key in exercise_lower:
            return weight_info
    
    return None


def _parse_ai_workout_response(ai_response: str) -> List[Dict[str, Any]]:
    """Parse AI response into structured exercise data."""
    exercises = []
    
    lines = ai_response.strip().split('\n')
    current_exercise = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if re.match(r'^\d+\.', line) or line.startswith('**') or line.startswith('#'):
            if current_exercise:
                exercises.append(current_exercise)
            
            exercise_name = re.sub(r'^\d+\.\s*', '', line)
            exercise_name = re.sub(r'\*\*', '', exercise_name)
            exercise_name = re.sub(r'^#+\s*', '', exercise_name)
            exercise_name = exercise_name.strip()
            
            current_exercise = {
                "name": exercise_name,
                "sets": 3,
                "reps": "8-12",
                "rest": "60-90 seconds",
                "notes": ""
            }
        elif current_exercise and ('sets' in line.lower() or 'reps' in line.lower()):
            sets_match = re.search(r'(\d+)\s*sets?', line, re.IGNORECASE)
            reps_match = re.search(r'(\d+(?:-\d+)?)\s*reps?', line, re.IGNORECASE)
            rest_match = re.search(r'(\d+(?:-\d+)?)\s*(?:seconds?|mins?|minutes?)', line, re.IGNORECASE)
            
            if sets_match:
                current_exercise["sets"] = int(sets_match.group(1))
            if reps_match:
                current_exercise["reps"] = reps_match.group(1)
            if rest_match:
                current_exercise["rest"] = rest_match.group(0)
        elif current_exercise and line:
            if current_exercise["notes"]:
                current_exercise["notes"] += " " + line
            else:
                current_exercise["notes"] = line
    
    if current_exercise:
        exercises.append(current_exercise)
    
    if not exercises:
        exercises = [{
            "name": "Push-ups",
            "sets": 3,
            "reps": "8-12",
            "rest": "60 seconds",
            "notes": "Bodyweight exercise"
        }]
    
    return exercises


async def _apply_weight_suggestions(exercises: List[Dict[str, Any]], fitness_level: str) -> List[Dict[str, Any]]:
    """Apply weight suggestions and exercise template matching to exercises."""
    enhanced_exercises = []
    
    for exercise in exercises:
        enhanced_exercise = exercise.copy()
        
        try:
            template_match = await match_exercise_template(exercise["name"])
            enhanced_exercise["template_id"] = template_match["template_id"]
            enhanced_exercise["matched_name"] = template_match["name"]
        except Exception:
            enhanced_exercise["template_id"] = "other_notes"
            enhanced_exercise["matched_name"] = f"Other – Notes - {exercise['name']}"
        
        weight_suggestion = _suggest_weight_for_exercise(exercise["name"], fitness_level)
        if weight_suggestion:
            enhanced_exercise["suggested_weight"] = weight_suggestion
        
        enhanced_exercises.append(enhanced_exercise)
    
    return enhanced_exercises


def _build_workout_prompt(constraints: WorkoutConstraints, overrides: Optional[WorkoutOverrides], template: str) -> str:
    """Build the workout prompt from constraints, overrides, and template."""
    goals_str = ", ".join(constraints.goals) if constraints.goals else "general fitness"
    equipment_str = ", ".join(constraints.equipment) if constraints.equipment else "bodyweight only"
    
    prompt_variables = {
        "goals": goals_str,
        "equipment": equipment_str,
        "duration": constraints.duration,
        "fitness_level": constraints.fitness_level
    }
    
    formatted_prompt = template.format(**prompt_variables)
    
    if overrides:
        if overrides.specific_exercises:
            formatted_prompt += f"\n\nPlease include these specific exercises: {', '.join(overrides.specific_exercises)}"
        
        if overrides.avoid_exercises:
            formatted_prompt += f"\n\nPlease avoid these exercises: {', '.join(overrides.avoid_exercises)}"
        
        if overrides.focus_areas:
            formatted_prompt += f"\n\nFocus on these body areas: {', '.join(overrides.focus_areas)}"
    
    return formatted_prompt


async def generate_workout(request: GenerateWorkoutRequest) -> Dict[str, Any]:
    """Generate a workout using AI based on constraints and overrides."""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        from main import prompts
        
        if "single_workout" not in prompts:
            raise HTTPException(
                status_code=500,
                detail="Single workout prompt template not found"
            )
        
        template = prompts["single_workout"]
        
        formatted_prompt = _build_workout_prompt(request.constraints, request.overrides, template)
        
        ai_response = await send_prompt(
            prompt=formatted_prompt,
            variables={},
            user_id=request.user_id
        )
        
        exercises = _parse_ai_workout_response(ai_response)
        
        enhanced_exercises = await _apply_weight_suggestions(
            exercises, 
            request.constraints.fitness_level
        )
        
        workout = Workout(
            date=datetime.now(),
            exercises=enhanced_exercises
        )
        
        return workout.model_dump()
        
    except ValueError as e:
        if "OpenRouter API key not found" in str(e):
            raise HTTPException(
                status_code=400,
                detail="OpenRouter API key not found in user settings"
            )
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate workout: {str(e)}"
        )
