from django.db import models


class Athlete(models.Model):
    """ Athlete model. """
    name = models.CharField(max_length=255)
    nationality_and_domestic_market = models.CharField(max_length=255)
    age = models.PositiveSmallIntegerField()
    gender = models.CharField(max_length=15, default="male",choices=(
        ("male", "Male"), ("female", "Female"),
    ))
    location_market = models.CharField(max_length=255)
    team = models.CharField(max_length=255)
    category = models.CharField(max_length=255, choices=(
        ("Football", "Football"),
        ("Rugby", "Rugby"),
        ("Athletics", "Athletics"),
        ("Cycling", "Cycling"),
        ("Swimming", "Swimming"),
        ("Gymnastics", "Gymnastics"),
        ("Golf", "Golf"),
        ("American Football", "American Football"),
        ("Basketball", "Basketball"),
        ("Baseball", "Baseball"),
        ("College Football", "College Football"),
        ("College Basketball", "College Basketball"),
        ("Ice Hockey", "Ice Hockey")
    ))
    marketability = models.PositiveSmallIntegerField(choices=(
        (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)
    ))
    optimal_campaign_time = models.PositiveSmallIntegerField(choices=(
        (1, "January"),
        (2, "February"),
        (3, "March"),
        (4, "April"),
        (5, "May"),
        (6, "June"),
        (7, "July"),
        (8, "August"),
        (9, "September"),
        (10, "October"),
        (11, "November"),
        (12, "December")
    ))
    market_transfer = models.BooleanField()
    instagram = models.BigIntegerField()
    twiter = models.BigIntegerField()

    def __str__(self):
        return self.name
