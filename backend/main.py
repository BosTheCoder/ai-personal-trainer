from dotenv import load_dotenv
from fastapi import FastAPI
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database'))
from migrate import migrate_database

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
