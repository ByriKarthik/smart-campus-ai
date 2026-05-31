import os

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_ai.settings')

app = Celery("campus_ai")

app.config_from_object(
    "django.conf:settings",
    namespace="CELERY"
)

app.conf.broker_url = (
    f"redis://{os.getenv('REDIS_HOST', 'redis')}:"
    f"{os.getenv('REDIS_PORT', '6379')}/0"
)

app.conf.result_backend = (
    f"redis://{os.getenv('REDIS_HOST', 'redis')}:"
    f"{os.getenv('REDIS_PORT', '6379')}/0"
)

app.autodiscover_tasks()