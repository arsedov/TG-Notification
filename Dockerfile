FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Command to run the application
# We use shell form to allow environment variable expansion for PORT if needed, 
# but fixed 8000 inside container is standard for docker-compose mapping.
CMD ["uvicorn", "main.py:app", "--host", "0.0.0.0", "--port", "8000"]
