# Generated by Django 2.1 on 2018-09-19 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_auto_20180919_0625'),
    ]

    operations = [
        migrations.AlterField(
            model_name='athlete',
            name='photo',
            field=models.URLField(default='https://cdn.mkeda.me/athletes/img/no-avatar.png', max_length=400),
        ),
    ]