gunicorn src.wsgi:application --workers 1 --threads 2 --worker-class gthread --timeout 120 --bind 0.0.0.0:$PORT
worker: celery -A your_project_name worker --loglevel=info