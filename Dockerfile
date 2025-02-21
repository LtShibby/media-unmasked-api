# Use Python Slim Image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Set PYTHONPATH (simplified)
ENV PYTHONPATH=/app

# Expose FastAPI's default port
EXPOSE 7860

# Start FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
