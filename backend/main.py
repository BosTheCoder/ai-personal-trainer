import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI

database_path = os.path.join(os.path.dirname(__file__), "..", "database")
if database_path not in sys.path:
    sys.path.append(database_path)

from migrate import migrate_database  # noqa: E402

load_dotenv()

app = FastAPI(title="AI Personal Trainer API", version="1.0.0")


@app.on_event("startup")
async def startup_event():
    migrate_database()


@app.get("/")
async def root():
    return {"message": "AI Personal Trainer API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
