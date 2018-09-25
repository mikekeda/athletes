# Generated by Django 2.1 on 2018-09-24 05:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_auto_20180921_1127'),
    ]

    operations = [
        migrations.AlterField(
            model_name='athlete',
            name='category',
            field=models.CharField(blank=True, choices=[('American Football', 'American Football'), ('Australian Football', 'Australian Football'), ('Athletics', 'Athletics'), ('Baseball', 'Baseball'), ('Basketball', 'Basketball'), ('College Basketball', 'College Basketball'), ('College Football', 'College Football'), ('Cricket', 'Cricket'), ('Cycling', 'Cycling'), ('Football', 'Football'), ('Golf', 'Golf'), ('Gymnastics', 'Gymnastics'), ('Handball', 'Handball'), ('Ice Hockey', 'Ice Hockey'), ('Rugby', 'Rugby'), ('Swimming', 'Swimming')], max_length=255),
        ),
        migrations.AlterField(
            model_name='team',
            name='category',
            field=models.CharField(blank=True, choices=[('American Football', 'American Football'), ('Australian Football', 'Australian Football'), ('Athletics', 'Athletics'), ('Baseball', 'Baseball'), ('Basketball', 'Basketball'), ('College Basketball', 'College Basketball'), ('College Football', 'College Football'), ('Cricket', 'Cricket'), ('Cycling', 'Cycling'), ('Football', 'Football'), ('Golf', 'Golf'), ('Gymnastics', 'Gymnastics'), ('Handball', 'Handball'), ('Ice Hockey', 'Ice Hockey'), ('Rugby', 'Rugby'), ('Swimming', 'Swimming')], max_length=255),
        ),
    ]