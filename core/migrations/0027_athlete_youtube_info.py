# Generated by Django 2.1 on 2018-09-20 18:36

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_auto_20180920_1646'),
    ]

    operations = [
        migrations.AddField(
            model_name='athlete',
            name='youtube_info',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict),
        ),
    ]
