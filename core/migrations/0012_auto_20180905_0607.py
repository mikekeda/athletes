# Generated by Django 2.1 on 2018-09-05 06:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20180904_1512'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='athlete',
            name='height',
        ),
        migrations.RemoveField(
            model_name='athlete',
            name='website',
        ),
        migrations.RemoveField(
            model_name='athlete',
            name='weight',
        ),
    ]
