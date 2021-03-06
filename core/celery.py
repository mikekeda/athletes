import os

from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "athletes.settings")

app = Celery("athletes")

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "every-sunday": {
        "task": "core.tasks.weekly_twitter_update",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),
        "args": (),
    },
    "every-monday-1": {
        "task": "core.tasks.weekly_athletes_youtube_update",
        "schedule": crontab(hour=3, minute=0, day_of_week=1),
        "args": (),
    },
    "every-monday-2": {
        "task": "core.tasks.weekly_trends_notifications",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),
        "args": (True,),
    },
    "every-monday-3": {
        "task": "core.tasks.weekly_trends_notifications",
        "schedule": crontab(hour=8, minute=30, day_of_week=1),
        "args": (),
    },
    "every-tuesday": {  # long time update
        "task": "core.tasks.weekly_athletes_twitter_update",
        "schedule": crontab(hour=0, minute=0, day_of_week=2),
        "args": (),
    },
    "every-wednesday": {
        "task": "core.tasks.weekly_awis_update",
        "schedule": crontab(hour=3, minute=0, day_of_week=3),
        "args": (),
    },
    "every-thursday": {
        "task": "core.tasks.weekly_stock_update",
        "schedule": crontab(hour=3, minute=0, day_of_week=4),
        "args": (),
    },
    "every-friday": {
        "task": "core.tasks.weekly_wiki_views_update",
        "schedule": crontab(hour=3, minute=0, day_of_week=5),
        "args": (),
    },
    "every-saturday": {
        "task": "core.tasks.weekly_youtube_update",
        "schedule": crontab(hour=3, minute=0, day_of_week=6),
        "args": (),
    },
    "every-day-1": {
        "task": "core.tasks.daily_update_notifications",
        "schedule": crontab(hour=9, minute=0),
        "args": (),
    },
    "every-day-2": {
        "task": "core.tasks.daily_teams_news_update",
        "schedule": crontab(hour=11, minute=0),
        "args": (),
    },
    "every-minute": {
        "task": "core.tasks.every_minute_twitter_update",
        "schedule": 60.0,
        "args": (),
    },
}
