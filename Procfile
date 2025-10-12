web: gunicorn src.wsgi:application
worker: celery -A src worker -l info