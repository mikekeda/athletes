from django.db import migrations
from django.db.utils import ProgrammingError
from core.models import COUNTRIES, Athlete


class Migration(migrations.Migration):
    def add_event_rules(apps, schema_editor):
        mapping = {val: key for key, val in COUNTRIES.items()}
        mapping.update({
            'England': 'GB',
            'United Kingdom': 'GB',
            'United States America': 'US',
            'Ivory Coast': 'CI',
            'Northern Ireland': 'GB',
        })

        try:
            for athlete in Athlete.objects.all():
                athlete.nationality_and_domestic_market = mapping.get(
                    athlete.nationality_and_domestic_market,
                    'zz'
                )
                athlete.location_market = mapping.get(
                    athlete.location_market,
                    'zz'
                )
                athlete.save()
        except ProgrammingError:
            pass

    dependencies = [
        ('core', '0002_athlete_gender'),
    ]

    operations = [
        migrations.RunPython(add_event_rules),
    ]
