"""
AI Personal Trainer Backend
FastAPI application placeholder
"""

from fastapi import FastAPI

app = FastAPI(title="AI Personal Trainer API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "AI Personal Trainer API is running"}
