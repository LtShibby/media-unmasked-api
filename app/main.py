import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from app.routers import analyze, health

# FastAPI app setup
app = FastAPI(title="MediaUnmasked API")

# ✅ Enable CORS for Swagger UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or specify ["http://localhost:7860"] for local testing)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Connected to Supabase successfully!")
else:
    print("Supabase connection failed. Please check your secrets.")

# Include routers for analysis and health
app.include_router(analyze.router, prefix="/api")
app.include_router(health.router, prefix="/health")

# Test root endpoint to confirm the API is running
@app.get("/")
async def root():
    return {"message": "MediaUnmasked API is running!"}
