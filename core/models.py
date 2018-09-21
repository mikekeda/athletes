from bs4 import BeautifulSoup
from bs4.element import Tag
import datetime
import logging
import requests
from requests_oauthlib import OAuth1
import urllib.parse

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from core.constans import (CATEGORIES, WIKI_CATEGORIES, COUNTRIES,
                           WIKI_COUNTRIES, WIKI_NATIONALITIES)


log = logging.getLogger('athletes')

auth = OAuth1(
    settings.TWITTER_APP_KEY,
    settings.TWITTER_APP_SECRET,
    settings.TWITTER_OAUTH_TOKEN,
    settings.TWITTER_OAUTH_TOKEN_SECRET
)


class Team(models.Model):
    wiki = models.URLField(unique=True)
    team = models.CharField(max_length=255, blank=True)
    photo = models.URLField(
        default='https://cdn.mkeda.me/athletes/img/no-avatar.png',
        max_length=600
    )
    location_market = models.CharField(
        max_length=2,
        blank=True,
        choices=COUNTRIES.items(),
    )
    gender = models.CharField(
        max_length=15,
        blank=True,
        choices=(("male", _("Male")), ("female", _("Female"))),
    )
    category = models.CharField(max_length=255, blank=True,
                                choices=CATEGORIES.items())
    additional_info = JSONField(default=dict, blank=True)
    longitude = models.FloatField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def photo_preview(self):
        return format_html('<img src="{}"/>', self.photo)

    def get_data_from_wiki(self, soup=None):
        """ Get information about team from Wiki. """
        log.info(f"Parsing Team {self.wiki}")

        if not soup:
            html = requests.get(self.wiki)
            if html.status_code != 200:
                # Team page doesn't exist.
                log.warning(f"Skipping Team {self.wiki} ({html.status_code})")
                return

            soup = BeautifulSoup(html.content, 'html.parser')

        card = soup.find("table", {"class": "vcard"})
        info = {}

        if not card or card.parent.attrs.get('role') == "navigation":
            # Team page doesn't have person card - skip.
            log.warning(f"Skipping Team {self.wiki} (no person card)")
            return

        img = card.select_one('img')
        if img and img.get('src'):
            self.photo = 'https://' + img['src'].strip('//')

        for row in card.find_all('tr'):
            td = row.find_all(recursive=False)
            if td:
                key = str(td[0].string or td[0].text).replace('\xa0', ' ')
                val = str(td[1].text).strip() if len(td) > 1 else ''

                info[key] = val

        self.additional_info = info

        return self.additional_info

    def get_location(self):
        """ Get team location (latitude and longitude). """
        log.info(f"Geocoding Team {self.team}")

        if self.additional_info:
            address = self.additional_info.get(
                'Ground') or self.additional_info.get(
                'Location') or self.additional_info.get(
                'Stadium')
            if address:
                url = (
                    f"https://maps.googleapis.com/maps/api/geocode/json"
                    f"?address={address}"
                    f"&key={settings.GEOCODING_API_KEY}"
                    f"&components=country:{self.location_market}"
                )
                res = requests.get(url)
                if res.status_code == 200:
                    geo_data = res.json()
                    if geo_data['results']:
                        self.longitude = geo_data['results'][0]['geometry'][
                            'location']['lng']
                        self.latitude = geo_data['results'][0]['geometry'][
                            'location']['lat']

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.team:
            # If team isn't set - send request to Wiki to get athlete info.
            self.get_data_from_wiki()

        # Get team location (latitude and longitude).
        if not self.latitude or not self.longitude:
            self.get_location()

        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)

    def __str__(self):
        return self.team


class Athlete(models.Model):
    """ Athlete model. """
    wiki = models.URLField(unique=True)
    name = models.CharField(max_length=255, blank=True)
    photo = models.URLField(
        default='https://cdn.mkeda.me/athletes/img/no-avatar.png',
        max_length=600
    )
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
    team_model = models.ForeignKey(
        Team,
        null=True,
        blank=True,
        related_name='members',
        on_delete=models.SET_NULL
    )
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
    international = models.BooleanField(default=False)
    instagram = models.PositiveIntegerField(null=True, blank=True)
    twitter = models.PositiveIntegerField(null=True, blank=True)
    additional_info = JSONField(default=dict, blank=True)
    twitter_info = JSONField(default=dict, blank=True)
    youtube_info = JSONField(default=dict, blank=True)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def age(self):
        today = datetime.date.today()
        return today.year - self.birthday.year - ((today.month, today.day) < (
            self.birthday.month, self.birthday.day))

    @property
    def market_export(self):
        return self.domestic_market != self.location_market

    @property
    def slug(self):
        return self.wiki.split('/')[-1]

    def photo_preview(self):
        return format_html('<img src="{}"/>', self.photo)

    def get_data_from_wiki(self):
        """ Get information about athlete from Wiki. """
        log.info(f"Parsing Athlete {self.wiki}")
        html = requests.get(self.wiki)
        if html.status_code != 200:
            # Athlete page doesn't exist.
            log.warning(f"Skipping Athlete {self.wiki} ({html.status_code})")
            return

        soup = BeautifulSoup(html.content, 'html.parser')
        card = soup.find("table", {"class": "vcard"})
        info = {}

        if not card or card.parent.attrs.get('role') == "navigation":
            # Athlete page doesn't have person card - skip.
            log.warning(f"Skipping Athlete {self.wiki} (no person card)")
            return

        # Get name.
        name = card.select(".fn") or soup.find_all("caption")
        if name:
            self.name = name[0].string or name[0].contents[0]
            if isinstance(self.name, Tag):
                self.name = self.name.string or self.name.text
        else:
            self.name = soup.title.string.split(' - Wikipedia')[0]

        # Get birthday.
        bday = card.find("span", {"class": "bday"})
        if not bday:
            # Athlete page doesn't have person card - skip.
            log.warning(f"Skipping Athlete {self.wiki} (no birthday)")
            return

        self.birthday = datetime.datetime.strptime(bday.string, "%Y-%m-%d")
        if self.age > 45:
            log.warning(f"Skipping Athlete {self.wiki} (too old)")
            return

        self.international = False

        img = card.select_one('img')
        if img and img.get('src'):
            self.photo = 'https://' + img['src'].strip('//')

        for row in card.find_all('tr'):
            td = row.find_all(recursive=False)
            if len(td) > 0:
                key = str(td[0].string or td[0].text).replace('\xa0', ' ')
                val = str(td[1].text).strip() if len(td) > 1 else ''

                self.international |= 'national team' in key.lower()
                info[key] = val

            if len(td) > 1:
                key = str(td[0].string).replace('\xa0', ' ')
                val = str(td[1].text).strip()

                if not self.team and key in ("Current team", "Club"):
                    # Get team.
                    self.team = val
                elif not self.category and \
                        key in ("Sport", "Discipline", "League") and \
                        val.capitalize() in WIKI_CATEGORIES:
                    # Get category.
                    self.category = WIKI_CATEGORIES[val.capitalize()]
                    if val == "NBA":
                        # NBA it's always US.
                        self.location_market = "US"
                elif not self.location_market and key == "Country":
                    # Get location_market.
                    location_market = td[1].find("a").string
                    if location_market in WIKI_COUNTRIES:
                        self.location_market = WIKI_COUNTRIES[location_market]
                elif not self.domestic_market and key == "Nationality":
                    # Get domestic_market.
                    if val in WIKI_NATIONALITIES:
                        self.domestic_market = WIKI_NATIONALITIES[val]
                elif not self.domestic_market and key == "Place of birth":
                    # Get domestic_market.
                    country = val.split(',')[-1].strip()
                    if country in WIKI_COUNTRIES:
                        self.domestic_market = WIKI_COUNTRIES[country]

        self.additional_info = info
        log.debug(info)

        return self.additional_info

    def get_location(self):
        """ Get athlete domestic_market with geocoding. """
        log.info(f"Geocoding Athlete {self.name}")

        if not self.additional_info:
            self.get_data_from_wiki()

        if self.additional_info and isinstance(self.additional_info, dict):
            address = self.additional_info.get(
                'Place of birth') or self.additional_info.get(
                'Born') or self.additional_info.get(
                'High school') or self.additional_info.get(
                'College') or self.additional_info.get(
                'Nationality')
            if address:
                url = (
                    "https://maps.googleapis.com/maps/api/geocode/json"
                    f"?address={address}"
                    f"&key={settings.GEOCODING_API_KEY}"
                )
                res = requests.get(url)
                if res.status_code == 200:
                    geo_data = res.json()
                    if geo_data['results']:
                        for component in \
                                geo_data['results'][0]['address_components']:
                            if 'country' in component['types'] and \
                                    component['short_name'] in COUNTRIES:
                                self.domestic_market = component['short_name']
                                log.info(f"Found {self.domestic_market}")
                                return component['short_name']

    def get_twitter_info(self):
        """ Get info from Twitter. """
        log.info(f"Get info from Twitter for Athlete {self.name}")
        self.twitter_info = {}

        urlencoded_name = urllib.parse.quote_plus(self.name)

        url = (
            "https://api.twitter.com/1.1/users/search.json"
            "?count=1"  # we need only 1
            f"&q={urlencoded_name} {self.category}"
        )
        res = requests.get(url, auth=auth)
        if res.status_code == 200:
            twitter_info = res.json()
            if twitter_info:
                self.twitter = twitter_info[0]['followers_count']
                self.twitter_info = twitter_info[0]
            else:
                log.info(f"No twitter info for Athlete {self.name}")
        else:
            log.warning(f"Failed getting twitter info for Athlete {self.name}")

        return self.twitter_info

    def get_youtube_info(self):
        """ Get info from Youtube. """
        log.info(f"Get info from Youtube for Athlete {self.name}")
        self.youtube_info = {}

        urlencoded_name = urllib.parse.quote_plus(self.name)

        url = (
            "https://www.googleapis.com/youtube/v3/search"
            "?maxResults=1"  # we need only 1
            "&type=channel"
            "&part=snippet"
            f"&regionCode={self.location_market}"
            f"&key={settings.GEOCODING_API_KEY}"
            f"&q={urlencoded_name}"
        )
        res = requests.get(url)
        if res.status_code == 200:
            youtube_info = res.json()
            if youtube_info and youtube_info['items']:
                channel_id = youtube_info['items'][0]['id']['channelId']
                url = (
                    "https://www.googleapis.com/youtube/v3/channels"
                    f"?id={channel_id}"
                    "&part=snippet,statistics"
                    f"&key={settings.GEOCODING_API_KEY}"
                )
                res = requests.get(url)
                if res.status_code == 200:
                    youtube_info = res.json()
                    if youtube_info and youtube_info['items']:
                        self.youtube_info = youtube_info['items'][0][
                            'statistics']
                        self.youtube_info.update(youtube_info['items'][0][
                                                     'snippet'])
            else:
                log.info(f"No youtube info for Athlete {self.name}")
        else:
            log.warning(f"Failed getting youtube info for Athlete {self.name}")

        return self.youtube_info

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.name:
            # If name isn't set - send request to Wiki to get athlete info.
            self.get_data_from_wiki()

        if not self.domestic_market:
            # Try to geolocate domestic_market.
            self.get_location()

        if not self.twitter_info:
            # Try to get amount od followers from twitter.
            self.get_twitter_info()

        if not self.get_youtube_info:
            # Try to get youtube info.
            self.get_youtube_info()

        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)

    def __str__(self):
        return self.name
