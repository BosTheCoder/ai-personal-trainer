import os
import sys
from typing import Dict

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

database_path = os.path.join(os.path.dirname(__file__), "..", "database")
if database_path not in sys.path:
    sys.path.append(database_path)

from migrate import migrate_database  # noqa: E402

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
