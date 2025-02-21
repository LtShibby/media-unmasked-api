from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # ✅ Import this
from app.routers import analyze, health

app = FastAPI(title="MediaUnmasked API")

# ✅ Enable CORS for Swagger UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or specify ["http://localhost:7860"])
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(analyze.router, prefix="/api")
app.include_router(health.router, prefix="/health")

@app.get("/")
async def root():
    return {"message": "MediaUnmasked API is running!"}
