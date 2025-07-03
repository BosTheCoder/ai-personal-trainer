from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class Goal(BaseModel):
    """Represents a fitness goal with template reference"""

    name: str = Field(..., description="Name of the goal")
    description: str = Field(..., description="Description of the goal")
    template_id: str = Field(..., description="ID of the associated template")


class ExerciseTemplateRef(BaseModel):
    """Reference to an exercise template"""

    template_id: str = Field(
        ..., description="Unique identifier for the exercise template"
    )
    name: str = Field(..., description="Name of the exercise")


class Workout(BaseModel):
    """Represents a single workout session"""

    id: str = Field(..., description="Unique identifier for the workout")
    date: datetime = Field(..., description="Date and time of the workout")
    exercises: List[ExerciseTemplateRef] = Field(
        default_factory=list, description="List of exercises in the workout"
    )


class WorkoutPlan(BaseModel):
    """Represents a complete workout plan spanning multiple weeks"""

    id: str = Field(..., description="Unique identifier for the workout plan")
    start_date: datetime = Field(..., description="Start date of the workout plan")
    weeks: int = Field(..., ge=1, description="Number of weeks in the plan")
    workouts: List[Workout] = Field(
        default_factory=list, description="List of workouts in the plan"
    )


class UserSettings(BaseModel):
    """User settings and preferences"""

    user_id: str = Field(..., description="Unique identifier for the user")
    goals: List[Goal] = Field(
        default_factory=list, description="List of user's fitness goals"
    )
    api_keys: Dict[str, Any] = Field(
        default_factory=dict, description="API keys and configuration"
    )


class HevySyncToken(BaseModel):
    """Token for Hevy app synchronization"""

    access_token: str = Field(..., description="Access token for Hevy API")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
