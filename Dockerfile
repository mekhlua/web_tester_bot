FROM mcr.microsoft.com/playwright/python:v1.62.0-noble

WORKDIR /app

# Install Python dependencies first (better Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Collect static files (for Django admin CSS etc.)
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Run migrations then start the production server
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py create_default_superuser && gunicorn webtester.wsgi:application --bind 0.0.0.0:8000"]
