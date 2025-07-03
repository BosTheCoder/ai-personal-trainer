from fastapi import FastAPI

app = FastAPI(title="AI Personal Trainer API", version="1.0.0")


@app.get("/")
async def root():
    return {"message": "AI Personal Trainer API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
