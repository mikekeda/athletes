from django.db import migrations


class Migration(migrations.Migration):
    def add_event_rules(self, schema_editor):
        pass

    dependencies = [
        ('core', '0002_athlete_gender'),
    ]

    operations = [
        migrations.RunPython(add_event_rules),
    ]
