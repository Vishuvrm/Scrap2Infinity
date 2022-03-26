web: gunicorn start:app
worker: celery -A Scrap2Infinity.app.celery worker --loglevel=INFO --pool=solo