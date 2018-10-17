import os

from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'athletes.settings')

app = Celery('athletes')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'every-monday': {
        'task': 'core.tasks.weekly_athletes_youtube_update',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),
        'args': ()
    },
    'every-saturday': {
        'task': 'core.tasks.weekly_youtube_update',
        'schedule': crontab(hour=3, minute=0, day_of_week=6),
        'args': ()
    },
}

app.conf.timezone = 'UTC'
