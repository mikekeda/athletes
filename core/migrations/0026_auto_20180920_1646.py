# Generated by Django 2.1 on 2018-09-20 16:46

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_auto_20180919_1655'),
    ]

    operations = [
        migrations.AlterField(
            model_name='athlete',
            name='twitter_info',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict),
        ),
    ]