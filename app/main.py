import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, AsyncClient
from app.routers import analyze, health

# Load environment variables first
load_dotenv()

# FastAPI app setup
app = FastAPI(title="MediaUnmasked API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Print environment variables for debugging
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
print(f"SUPABASE_KEY: {os.getenv('SUPABASE_KEY')}")

# Initialize Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    print("Supabase credentials loaded successfully!")
else:
    print("Warning: Supabase credentials not found in environment variables")

# Include routers for analysis and health
app.include_router(analyze.router, prefix="/api")
app.include_router(health.router, prefix="/health")

# Test root endpoint to confirm the API is running
@app.get("/")
async def root():
    return {"message": "MediaUnmasked API is running!"}
