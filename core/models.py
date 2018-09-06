from bs4 import BeautifulSoup
import datetime
import logging
import requests

from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.constans import (CATEGORIES, WIKI_CATEGORIES, COUNTRIES,
                           WIKI_COUNTRIES, WIKI_NATIONALITIES)


logger = logging.getLogger(__name__)


class Athlete(models.Model):
    """ Athlete model. """
    wiki = models.URLField(unique=True)
    name = models.CharField(max_length=255, blank=True)
    domestic_market = models.CharField(
        max_length=2,
        blank=True,
        choices=COUNTRIES.items(),
    )
    birthday = models.DateField(blank=True)
    gender = models.CharField(
        max_length=15,
        blank=True,
        choices=(("male", _("Male")), ("female", _("Female"))),
    )
    location_market = models.CharField(
        max_length=2,
        blank=True,
        choices=COUNTRIES.items(),
    )
    team = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=255, blank=True,
                                choices=CATEGORIES.items())
    marketability = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=((1, 1), (2, 2), (3, 3), (4, 4), (5, 5)),
    )
    optimal_campaign = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=(
            (1, _("January")),
            (2, _("February")),
            (3, _("March")),
            (4, _("April")),
            (5, _("May")),
            (6, _("June")),
            (7, _("July")),
            (8, _("August")),
            (9, _("September")),
            (10, _("October")),
            (11, _("November")),
            (12, _("December"))
        )
    )
    market_transfer = models.BooleanField(null=True, blank=True)
    instagram = models.PositiveIntegerField(null=True, blank=True)
    twiter = models.PositiveIntegerField(null=True, blank=True)

    @property
    def age(self):
        today = datetime.date.today()
        return today.year - self.birthday.year - ((today.month, today.day) < (
            self.birthday.month, self.birthday.day))

    def get_data_from_wiki(self):
        """ Get information about athlete from Wiki. """
        html = requests.get(self.wiki)
        soup = BeautifulSoup(html.content, 'html.parser')
        card = soup.find("table", {"class": "vcard"})
        info = {}

        # Get name.
        name = card.select(".fn") or soup.findAll("caption")
        self.name = name[0].string or name[0].contents[0]

        # Get birthday.
        bday = card.find("span", {"class": "bday"}).string
        self.birthday = datetime.datetime.strptime(bday, "%Y-%m-%d")

        for row in card.findAll('tr'):
            td = row.find_all(recursive=False)
            if len(td) > 1:
                key = str(td[0].string).replace('\xa0', ' ')
                val = str(td[1].text).strip()

                if key in ("Current team", "Club"):
                    # Get team.
                    self.team = val
                elif key in ("Sport", "Discipline", "League") and \
                        val.capitalize() in WIKI_CATEGORIES:
                    # Get category.
                    self.category = WIKI_CATEGORIES[val.capitalize()]
                    if val == "NBA":
                        # NBA it's always US.
                        self.location_market = "US"
                elif key == "Country":
                    # Get location_market.
                    location_market = td[1].find("a").string
                    if location_market in WIKI_COUNTRIES:
                        self.location_market = WIKI_COUNTRIES[location_market]
                elif key == "Nationality":
                    # Get domestic_market.
                    if val in WIKI_NATIONALITIES:
                        self.domestic_market = WIKI_NATIONALITIES[val]

                info[key] = val

        logger.info(info)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.name:
            # If name isn't set - send request to Wiki to get athlete info.
            self.get_data_from_wiki()

        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)

    def __str__(self):
        return self.name
