from celery import Celery, shared_task

from core.models import Athlete


app = Celery('athletes')


@shared_task
def create_athlete_task(wiki, team):
    """ Task to crawl athletes from wiki team page. """
    athlete = Athlete.objects.filter(wiki=wiki).first()

    if not athlete:
        Athlete.objects.create(wiki=wiki, team=team)
    elif not athlete.team:
        athlete.team = team
        athlete.save()
