# Generated by Django 2.1.2 on 2018-11-07 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0044_auto_20181101_1300'),
    ]

    operations = [
        migrations.AlterField(
            model_name='athlete',
            name='category',
            field=models.CharField(blank=True, choices=[('American Football', 'American Football'), ('Australian Football', 'Australian Football'), ('Athletics', 'Athletics'), ('Baseball', 'Baseball'), ('Basketball', 'Basketball'), ('College Basketball', 'College Basketball'), ('College Football', 'College Football'), ('Cricket', 'Cricket'), ('Cycling', 'Cycling'), ('Football', 'Football'), ('Golf', 'Golf'), ('Gymnastics', 'Gymnastics'), ('Handball', 'Handball'), ('Ice Hockey', 'Ice Hockey'), ('Motorsport', 'Motorsport'), ('Rugby', 'Rugby'), ('Swimming', 'Swimming'), ('Tennis', 'Tennis')], max_length=255),
        ),
        migrations.AlterField(
            model_name='league',
            name='category',
            field=models.CharField(blank=True, choices=[('American Football', 'American Football'), ('Australian Football', 'Australian Football'), ('Athletics', 'Athletics'), ('Baseball', 'Baseball'), ('Basketball', 'Basketball'), ('College Basketball', 'College Basketball'), ('College Football', 'College Football'), ('Cricket', 'Cricket'), ('Cycling', 'Cycling'), ('Football', 'Football'), ('Golf', 'Golf'), ('Gymnastics', 'Gymnastics'), ('Handball', 'Handball'), ('Ice Hockey', 'Ice Hockey'), ('Motorsport', 'Motorsport'), ('Rugby', 'Rugby'), ('Swimming', 'Swimming'), ('Tennis', 'Tennis')], max_length=255),
        ),
        migrations.AlterField(
            model_name='team',
            name='category',
            field=models.CharField(blank=True, choices=[('American Football', 'American Football'), ('Australian Football', 'Australian Football'), ('Athletics', 'Athletics'), ('Baseball', 'Baseball'), ('Basketball', 'Basketball'), ('College Basketball', 'College Basketball'), ('College Football', 'College Football'), ('Cricket', 'Cricket'), ('Cycling', 'Cycling'), ('Football', 'Football'), ('Golf', 'Golf'), ('Gymnastics', 'Gymnastics'), ('Handball', 'Handball'), ('Ice Hockey', 'Ice Hockey'), ('Motorsport', 'Motorsport'), ('Rugby', 'Rugby'), ('Swimming', 'Swimming'), ('Tennis', 'Tennis')], max_length=255),
        ),
    ]
