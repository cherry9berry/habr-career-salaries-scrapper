FROM python:3.9-slim

WORKDIR /app

# Install PostgreSQL client for database setup
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make setup script executable
RUN chmod +x render_setup.sh

# Create temp directory for uploads
RUN mkdir -p /tmp

# Expose port for API
EXPOSE 8000

# Startup script that runs setup and then starts API
CMD ["sh", "-c", "./render_setup.sh && python run_api.py"] 