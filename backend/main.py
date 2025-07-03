import os
import sys
from typing import Dict

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from app.models import PromptTemplate

database_path = os.path.join(os.path.dirname(__file__), "..", "database")
if database_path not in sys.path:
    sys.path.append(database_path)

from migrate import migrate_database  # noqa: E402

from app.utils import match_exercise_template  # noqa: E402

load_dotenv()

app = FastAPI(title="AI Personal Trainer API", version="1.0.0")

prompts: Dict[str, str] = {}


def load_prompts():
    """Load prompt templates from prompts.yaml file"""
    global prompts
    prompts_file = os.path.join(os.path.dirname(__file__), "..", "prompts.yaml")

    try:
        with open(prompts_file, "r", encoding="utf-8") as file:
            loaded_prompts = yaml.safe_load(file)
            if loaded_prompts:
                prompts = loaded_prompts
                print(f"Loaded {len(prompts)} prompt templates")
            else:
                print("Warning: prompts.yaml is empty")
    except FileNotFoundError:
        print("Warning: prompts.yaml not found")
    except yaml.YAMLError as e:
        print(f"Error parsing prompts.yaml: {e}")


def save_prompts():
    """Save prompt templates to prompts.yaml file"""
    prompts_file = os.path.join(os.path.dirname(__file__), "..", "prompts.yaml")

    try:
        temp_file = prompts_file + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as file:
            yaml.safe_dump(prompts, file, default_flow_style=False, allow_unicode=True)

        os.replace(temp_file, prompts_file)
        print(f"Saved {len(prompts)} prompt templates to {prompts_file}")
    except Exception as e:
        temp_file = prompts_file + ".tmp"
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise e


@app.on_event("startup")
async def startup_event():
    migrate_database()
    load_prompts()


@app.get("/")
async def root():
    return {"message": "AI Personal Trainer API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/prompts/{name}")
async def get_prompt(name: str):
    """Get a prompt template by name"""
    if name not in prompts:
        available = list(prompts.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Prompt template '{name}' not found. Available: {available}",
        )

    return {"name": name, "template": prompts[name]}


@app.put("/prompts/{name}")
async def update_prompt(name: str, prompt_data: PromptTemplate):
    """Update a prompt template by name"""
    global prompts

    if name != prompt_data.name:
        raise HTTPException(
            status_code=400,
            detail=f"URL name '{name}' does not match request body name "
            f"'{prompt_data.name}'",
        )

    prompts[name] = prompt_data.template

    try:
        save_prompts()
        return {
            "name": name,
            "template": prompt_data.template,
            "message": "Prompt updated successfully",
        }
    except Exception as e:
        load_prompts()
        raise HTTPException(
            status_code=500, detail=f"Failed to save prompt to file: {str(e)}"
        )


@app.post("/exercise-templates/match")
async def match_exercise_endpoint(request: dict):
    """Match an exercise name to a Hevy template"""
    try:
        exercise_name = request.get("exercise_name", "")
        result = await match_exercise_template(exercise_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
