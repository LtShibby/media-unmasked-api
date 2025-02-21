# Use Python Slim Image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Install git (required to install from GitHub)
RUN apt-get update && apt-get install -y git

# Create a writable cache directory for Hugging Face
RUN mkdir -p /app/.cache/huggingface/hub && chmod -R 777 /app/.cache

# Install supabase-py directly from GitHub
RUN pip install --upgrade pip
RUN pip install git+https://github.com/supabase/supabase-py.git

# Copy dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy all files
COPY . .

# Set PYTHONPATH (simplified)
ENV PYTHONPATH=/app

# Set the Hugging Face transformers cache directory
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/hub

# Expose FastAPI's default port
EXPOSE 7860

# Start FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
