import logging
import time

from django.core.management import BaseCommand
from django.db.utils import DataError

from core.models import Athlete


log = logging.getLogger('athletes')


class Command(BaseCommand):
    # Show this when the user types help
    help = "Import athletes information from Twitter"

    def handle(self, *args, **options):
        self.stdout.write("Started Twitter import")

        aids = list(Athlete.objects.filter(twitter_info={}).values_list(
            'id',flat=True))

        self.stdout.write(f"{len(aids)} athletes to update")

        for aid in aids:
            athlete = Athlete.objects.get(id=aid)
            athlete.get_twitter_info()
            try:
                super(Athlete, athlete).save()
            except DataError as e:
                # Remove twitter_info and try to save one more time.
                log.warning(f"{athlete.name} {repr(e)}")
                athlete.twitter_info = {}
                super(Athlete, athlete).save()

            time.sleep(1)  # we have a limit (900 requests per 15m)
