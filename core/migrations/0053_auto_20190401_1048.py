# Generated by Django 2.1.7 on 2019-04-01 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0052_auto_20190321_2122'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teamarticle',
            name='urlToImage',
            field=models.URLField(max_length=512),
        ),
    ]
