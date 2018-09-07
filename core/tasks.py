from celery import Celery, shared_task
import logging

from django.db.utils import IntegrityError

from core.models import Athlete


app = Celery('athletes')
log = logging.getLogger('athletes')


@shared_task
def create_athlete_task(wiki, data):
    """ Task to crawl athletes from wiki team page. """
    athlete = Athlete.objects.filter(wiki=wiki).first()
    data = {key: val for key, val in data.items() if val}  # remove empty vals

    try:
        if not athlete:
            # Create an athlete.
            Athlete.objects.create(wiki=wiki, **data)
        else:
            # Update an athlete.
            for field in data:
                if not getattr(athlete, field):
                    setattr(athlete, field, data[field])
            athlete.save()
    except IntegrityError as e:
        log.warning(f"{repr(e)}: Skip athlete for {wiki}")
