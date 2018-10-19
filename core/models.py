import datetime
import logging
import urllib.parse
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from requests_oauthlib import OAuth1

from core.constans import (CATEGORIES, WIKI_CATEGORIES, COUNTRIES,
                           WIKI_COUNTRIES, WIKI_NATIONALITIES)

log = logging.getLogger('athletes')

auth = OAuth1(
    settings.TWITTER_APP_KEY,
    settings.TWITTER_APP_SECRET,
    settings.TWITTER_OAUTH_TOKEN,
    settings.TWITTER_OAUTH_TOKEN_SECRET
)


class ModelMixin:
    """ Mixin class that has common methods. """
    wiki = None
    name = None
    category = None
    location_market = None
    photo = None
    twitter = None
    twitter_info = {}
    youtube_info = {}

    @property
    def slug(self):
        return self.wiki.split('/')[-1]

    def photo_preview(self):
        return format_html(
            '<div class="w-100" style="background-image: url(&quot;{}&quot;); '
            'height: 200px; background-repeat: no-repeat; '
            'background-size: contain;"></div>',
            self.photo
        )

    def get_twitter_info(self):
        """ Get info from Twitter. """
        model = self.__class__.__name__
        if self.twitter_info.get('screen_name'):
            log.info(f"Update info from Twitter for {model} {self.name}")
            screen_name = self.twitter_info['screen_name']

            url = (
                "https://api.twitter.com/1.1/users/show.json"
                f"?screen_name={screen_name}"
            )

        else:
            log.info(f"Get info from Twitter for {model} {self.name}")
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
                if isinstance(twitter_info, list):
                    twitter_info = twitter_info[0]

                self.twitter = twitter_info['followers_count']
                self.twitter_info = twitter_info
            else:
                log.info(f"No twitter info for {model} {self.name}")
        else:
            log.warning(f"Failed getting twitter info for {model} {self.name} "
                        f"({res.status_code})")

        return self.twitter_info

    def get_youtube_info(self):
        """ Get info from Youtube. """
        model = self.__class__.__name__

        log.info(f"Get info from Youtube for {model} {self.name}")
        historical_keys = ('commentCount', 'subscriberCount', 'videoCount',
                           'viewCount')

        channel_id = self.youtube_info.get('channelId')
        history = self.youtube_info.get('history', {})
        now = datetime.datetime.now()
        if self.youtube_info:
            week_ago = str(now - datetime.timedelta(weeks=1))
            last_update = self.youtube_info.get('updated', week_ago)

            history[last_update] = {}
            for key in historical_keys:
                history[last_update][key] = self.youtube_info.get(key, 0)

        if not channel_id:
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
                if youtube_info and youtube_info['items'] and \
                        youtube_info['items'][0]['id'].get('channelId'):
                    channel_id = youtube_info['items'][0]['id']['channelId']
                else:
                    log.info(f"No youtube info for {model} {self.name}")
            else:
                log.warning(
                    f"Failed getting youtube info for {model} {self.name} "
                    f"({res.status_code})")

        if channel_id:
            url = (
                "https://www.googleapis.com/youtube/v3/channels"
                "?part=snippet,statistics"
                f"&key={settings.GEOCODING_API_KEY}"
                f"&id={channel_id}"
            )
            res = requests.get(url)
            if res.status_code == 200:
                youtube_info = res.json()
                if youtube_info and youtube_info['items']:
                    self.youtube_info = {'channelId': channel_id}
                    self.youtube_info.update(youtube_info['items'][0][
                                                 'statistics'])
                    self.youtube_info.update(youtube_info['items'][0][
                                                 'snippet'])
                    self.youtube_info['updated'] = str(now)
                    self.youtube_info['history'] = history
                else:
                    log.info("Updating youtube info: no data "
                             f"for {model} {self.name}")
            else:
                log.warning(f"Failed updating youtube info "
                            f"for {model} {self.name} ({res.status_code})")

        return self.youtube_info

    @property
    def get_youtube_stats(self):
        """ Youtube statistic (subscriberCount, viewCount). """
        stats = []
        if self.youtube_info.get('history'):
            history = self.youtube_info['history']
            last_update = self.youtube_info['updated']
            history[last_update] = {
                'subscriberCount': self.youtube_info.get('subscriberCount',
                                                         '0'),
                'viewCount': self.youtube_info.get('viewCount', '0'),
            }

            dates = sorted(history.keys(), reverse=True)
            for d in dates:
                stats.append([d[:10], [
                    int(history[d]['subscriberCount']),
                    int(history[d]['viewCount']),
                ]])

        return stats

    @property
    def get_youtube_weekly_stats(self):
        """ Youtube weekly statistic (subscriberCount, viewCount). """
        stats = []
        if self.youtube_info.get('history'):
            history = self.youtube_info['history']
            last_update = self.youtube_info['updated']
            history[last_update] = {
                'subscriberCount': self.youtube_info.get('subscriberCount',
                                                         '0'),
                'viewCount': self.youtube_info.get('viewCount', '0'),
            }

            dates = sorted(history.keys(), reverse=True)
            for i, d in enumerate(dates[:-1]):
                stats.append([d[:10], [
                    int(history[d]['subscriberCount']) - int(
                        history[dates[i + 1]]['subscriberCount']),
                    int(history[d]['viewCount']) - int(
                        history[dates[i + 1]]['viewCount']),
                ]])

        return stats


class League(models.Model, ModelMixin):
    wiki = models.URLField(unique=True)
    name = models.CharField(max_length=255, blank=True)
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
    twitter_info = JSONField(default=dict, blank=True)
    youtube_info = JSONField(default=dict, blank=True)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_data_from_wiki(self, soup=None):
        """ Get information about league from Wiki. """
        log.info(f"Parsing League {self.wiki}")

        if not soup:
            html = requests.get(self.wiki)
            if html.status_code != 200:
                # League page doesn't exist.
                log.warning(
                    f"Skipping League {self.wiki} ({html.status_code})"
                )
                return

            soup = BeautifulSoup(html.content, 'html.parser')

        card = soup.find("table", {"class": "infobox"})
        info = {}

        if not card or card.parent.attrs.get('role') == "navigation":
            # League page doesn't have person card - skip.
            log.warning(f"Skipping League {self.wiki} (no person card)")
            return

        # Get name.
        name = card.select(".fn") or soup.find_all("caption")
        if name:
            self.name = name[0].string or name[0].contents[0]
            if isinstance(self.name, Tag):
                self.name = self.name.string or self.name.text
        else:
            self.name = soup.title.string.split(' - Wikipedia')[0]

        if not card or card.parent.attrs.get('role') == "navigation":
            # League page doesn't have person card - skip.
            log.warning(f"Skipping League {self.wiki} (no person card)")
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

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.name:
            # If name isn't set - send request to Wiki to get additional info.
            self.get_data_from_wiki()

        if not self.twitter_info:
            # Try to get twitter info.
            self.get_twitter_info()

        if not self.youtube_info.get('updated'):
            # Try to get youtube info.
            self.get_youtube_info()

        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)

    def __str__(self):
        return self.name


class Team(models.Model, ModelMixin):
    wiki = models.URLField(unique=True)
    name = models.CharField(max_length=255, blank=True)
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
    league = models.ForeignKey(
        League,
        null=True,
        blank=True,
        related_name='teams',
        on_delete=models.SET_NULL
    )
    category = models.CharField(max_length=255, blank=True,
                                choices=CATEGORIES.items())
    longitude = models.FloatField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    additional_info = JSONField(default=dict, blank=True)
    twitter_info = JSONField(default=dict, blank=True)
    youtube_info = JSONField(default=dict, blank=True)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

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

        card = soup.find("table", {"class": "vcard"}) or soup.find(
            "table", {"class": "infobox"})
        info = {}
        site = urlparse(self.wiki)
        site = f'{site.scheme}://{site.hostname}'

        if not card or card.parent.attrs.get('role') == "navigation":
            # Team page doesn't have person card - skip.
            log.warning(f"Skipping Team {self.wiki} (no person card)")
            return

        img = card.select_one('a.image > img') or card.select_one('img')
        if img and img.get('src'):
            self.photo = 'https://' + img['src'].strip('//')

        for row in card.find_all('tr'):
            td = row.find_all(recursive=False)
            if td:
                key = str(td[0].string or td[0].text).replace('\xa0', ' ')
                val = str(td[1].text).strip() if len(td) > 1 else ''

                info[key] = val

                if key == 'League' and td[1] and not self.league:
                    link = td[1].find('a')
                    if not link or not link.get('href'):
                        continue

                    if link['href'][:4] != 'http':
                        link['href'] = site + link['href']

                    league, created = League.objects.get_or_create(
                        wiki=link['href'],
                        defaults={
                            'location_market': self.location_market,
                            'gender': self.gender,
                            'category': self.category,
                        }
                    )
                    self.league = league

        self.additional_info = info

        return self.additional_info

    def get_location(self):
        """ Get team location (latitude and longitude). """
        log.info(f"Geocoding Team {self.name}")

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
        if not self.name:
            # If name isn't set - send request to Wiki to get additional info.
            self.get_data_from_wiki()

        # Get team location (latitude and longitude).
        if not self.latitude or not self.longitude:
            self.get_location()

        if not self.twitter_info:
            # Try to get twitter info.
            self.get_twitter_info()

        if not self.youtube_info.get('updated'):
            # Try to get youtube info.
            self.get_youtube_info()

        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)

    def __str__(self):
        return self.name


class Athlete(models.Model, ModelMixin):
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
        validators=[
            MaxValueValidator(100)
        ]
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

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.name:
            # If name isn't set - send request to Wiki to get additional info.
            self.get_data_from_wiki()

        if not self.domestic_market:
            # Try to geolocate domestic_market.
            self.get_location()

        if not self.twitter_info:
            # Try to get amount od followers from twitter.
            self.get_twitter_info()

        if not self.youtube_info.get('updated'):
            # Try to get youtube info.
            self.get_youtube_info()

        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)

    def __str__(self):
        return self.name


class AthletesList(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    athletes = models.ManyToManyField(Athlete, related_name='athletes_lists')
    user = models.ForeignKey(
        User,
        related_name='athletes_lists',
        on_delete=models.CASCADE
    )
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TeamsList(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    teams = models.ManyToManyField(Team, related_name='teams_lists')
    user = models.ForeignKey(
        User,
        related_name='teams_lists',
        on_delete=models.CASCADE
    )
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class LeaguesList(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    leagues = models.ManyToManyField(League, related_name='leagues_lists')
    user = models.ForeignKey(
        User,
        related_name='leagues_lists',
        on_delete=models.CASCADE
    )
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class AthleteFollower(models.Model):
    athlete = models.ForeignKey(
        Athlete,
        related_name='followers',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name='followed_athletes',
        on_delete=models.CASCADE
    )
    added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.athlete.name}_{self.user.username}'
