from celery import Celery, shared_task

from core.models import Athlete


app = Celery('athletes')


@shared_task
def create_athlete_task(wiki, team):
    """ Task to crawl athletes from wiki team page. """
    if not Athlete.objects.filter(wiki=wiki).exists():
        Athlete.objects.create(wiki=wiki, team=team)
