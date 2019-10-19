from django.db import migrations
# from django.db.utils import ProgrammingError
# from core.models import Athlete
# from core.constans import REVERSED_COUNTRIES


class Migration(migrations.Migration):
    def add_event_rules(apps, schema_editor):
        pass
        # there is an error in test related to this migration
        # django.db.utils.InternalError: current transaction is aborted,
        # commands ignored until end of transaction block

        # mapping = REVERSED_COUNTRIES.copy()
        # mapping.update({
        #     'England': 'GB',
        #     'United Kingdom': 'GB',
        #     'United States America': 'US',
        #     'Ivory Coast': 'CI',
        #     'Northern Ireland': 'GB',
        # })
        #
        # try:
        #     for athlete in Athlete.objects.all():
        #         athlete.nationality_and_domestic_market = mapping.get(
        #             athlete.nationality_and_domestic_market,
        #             'zz'
        #         )
        #         athlete.location_market = mapping.get(
        #             athlete.location_market,
        #             'zz'
        #         )
        #         athlete.save()
        # except ProgrammingError:
        #     pass

    dependencies = [
        ('core', '0002_athlete_gender'),
    ]

    operations = [
        migrations.RunPython(add_event_rules),
    ]
