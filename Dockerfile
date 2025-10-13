# Use an official Python image
FROM python:3.12-slim

# Prevents Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get -y install gcc libpq-dev 
# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY .

# Expose Django port
EXPOSE 8000

# Default command (can be overridden by docker-compose)
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
