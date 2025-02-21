#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload
