# Generated by Django 2.1 on 2018-09-04 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20180904_1356'),
    ]

    operations = [
        migrations.AlterField(
            model_name='athlete',
            name='wiki',
            field=models.URLField(unique=True),
        ),
    ]
