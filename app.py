from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.routers import router as api_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Recipe App API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
