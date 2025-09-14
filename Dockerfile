# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Start server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "leave_management.wsgi:application"]

# docker-compose.yml
version: '3.8'

services:
web:
build: .
ports:
- "8000:8000"
volumes:
- .:/app
environment:
- DEBUG=True
depends_on:
- db

db:
image: mysql:8.0
environment:
MYSQL_DATABASE: leave_management
MYSQL_USER: leave_user
MYSQL_PASSWORD: leave_password
MYSQL_ROOT_PASSWORD: root_password
volumes:
- mysql_data:/var/lib/mysql
ports:
- "3306:3306"

volumes:
mysql_data: