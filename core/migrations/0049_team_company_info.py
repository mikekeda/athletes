# Generated by Django 2.1.3 on 2018-12-18 19:13

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0048_auto_20181129_1537'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='company_info',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict),
        ),
    ]