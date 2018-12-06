import datetime
import logging
import operator
import urllib.parse
import hmac
import hashlib
import xmltodict

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.cache import cache
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from core.constans import (
    CATEGORIES, WIKI_CATEGORIES, COUNTRIES,
    WIKI_COUNTRIES, WIKI_NATIONALITIES
)

log = logging.getLogger('athletes')


class ModelMixin:
    """ Mixin class that has common methods. """
    wiki = None
    name = None
    category = None
    location_market = None
    photo = None
    twitter = None
    additional_info = {}
    twitter_info = {}
    youtube_info = {}
    wiki_views_info = {}
    site_views_info = {}

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

    @staticmethod
    def geocode(address):
        """ Geocode the address. """
        log.info(f"Geocoding {address}")

        geo_data = {'results': []}

        url = (
            "https://maps.googleapis.com/maps/api/geocode/json"
            f"?address={address}"
            f"&key={settings.GEOCODING_API_KEY}"
        )
        res = requests.get(url)
        if res.status_code == 200:
            geo_data = res.json()

        return geo_data

    def get_wiki_views_info(self):
        """ Get visits from Wiki. """
        model = self.__class__.__name__

        log.info(f"Get visits from Wiki for {model} {self.name}")

        now = datetime.datetime.now()
        week_ago = now - datetime.timedelta(weeks=1)

        url = (
            "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
            "/en.wikipedia/all-access/all-agents"
            f"/{self.slug}"
            "/daily"
            f"/{str(week_ago)[:10].replace('-', '')}00"
            f"/{str(now)[:10].replace('-', '')}00"
        )
        res = requests.get(url)
        if res.status_code == 200:
            wiki_views_info = res.json()
            if wiki_views_info and wiki_views_info['items']:
                for item in wiki_views_info['items']:
                    key = '-'.join([
                        item['timestamp'][:4],
                        item['timestamp'][4:6],
                        item['timestamp'][6:8]
                    ])
                    self.wiki_views_info[key] = item['views']

        return self.wiki_views_info

    def get_twitter_info(self):
        """ Get info from Twitter. """
        cache.set(f'twitter_update_{self.__class__.__name__}_{self.pk}', '',
                  timeout=24*60*60)  # the key will expire in 1 day

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

    def get_awis_info(self, days_ago: int = 1):
        """ Get visits statistic from awis. """
        # Key derivation functions. See:
        # http://docs.aws.amazon.com/general/latest/gr
        # /signature-v4-examples.html#signature-v4-examples-python
        def sign(_key, msg):
            return hmac.new(_key, msg.encode('utf-8'),
                            hashlib.sha256).digest()

        def get_signature_key(_key, date_stamp):
            k_date = sign(('AWS4' + _key).encode('utf-8'), date_stamp)
            k_region = sign(k_date, 'us-west-1')
            k_service = sign(k_region, 'awis')
            k_signing = sign(k_service, 'aws4_request')
            return k_signing

        model = self.__class__.__name__

        log.info(f"Get visits statistic from awis for {model} {self.name}")

        website = self.additional_info.get('Website')
        if not website:
            log.info(f"{model} {self.name} doesn't have website")
            return {}

        now = datetime.datetime.now()
        day_ago = now - datetime.timedelta(days=days_ago)
        datestamp = now.strftime('%Y%m%d')
        amzdate = now.strftime('%Y%m%dT%H%M%SZ')

        canonical_querystring = urllib.parse.urlencode([
            ('Action', "UrlInfo"),
            ('Range', 7),
            ('ResponseGroup', 'UsageStats,RankByCountry'),
            ('Start', day_ago.strftime('%Y%m%d')),
            ('Url', website),
        ])

        url = f"https://awis.amazonaws.com/api?{canonical_querystring}"

        credential_scope = f'{datestamp}/us-west-1/awis/aws4_request'
        signing_key = get_signature_key(settings.AWS_SECRET_ACCESS_KEY,
                                        datestamp)
        payload_hash = hashlib.sha256(''.encode('utf8')).hexdigest()
        canonical_request = '\n'.join([
            'GET',
            '/api',
            canonical_querystring,
            'host:awis.us-west-1.amazonaws.com',
            f'x-amz-date:{amzdate}',
            '',
            'host;x-amz-date',
            payload_hash
        ])
        string_to_sign = '\n'.join([
            'AWS4-HMAC-SHA256',
            amzdate,
            credential_scope,
            hashlib.sha256(canonical_request.encode('utf8')).hexdigest()
        ])
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'),
                             hashlib.sha256).hexdigest()
        authorization_header = (
            f"AWS4-HMAC-SHA256 Credential={settings.AWS_ACCESS_ID}"
            f"/{datestamp}/us-west-1/awis/aws4_request, SignedHeaders=host;"
            f"x-amz-date, Signature={signature}"
        )

        headers = {
            'X-Amz-Date': amzdate,
            'Authorization': authorization_header,
            'Content-Type': 'application/xml',
            'Accept': 'application/xml'
        }

        res = requests.get(url, headers=headers)

        if res.status_code == 200:
            views_info = xmltodict.parse(res.content)
            if views_info and views_info.get('aws:UrlInfoResponse'):
                data = {'total': 0.0}
                root = views_info['aws:UrlInfoResponse']['aws:Response'][
                    'aws:UrlInfoResult']['aws:Alexa']['aws:TrafficData']
                for item in root['aws:UsageStatistics']['aws:UsageStatistic']:
                    if item['aws:TimeRange'].get('aws:Days') == '7':
                        data['total'] = round(
                            float(item['aws:PageViews']['aws:PerMillion'][
                                      'aws:Value']),
                            1
                        )
                        break

                records = root['aws:RankByCountry']['aws:Country']
                for row in records:
                    if isinstance(row, dict) and row['@Code'] in COUNTRIES:
                        data[row['@Code']] = round(
                            data['total'] / 100 * float(
                                row['aws:Contribution']['aws:PageViews'][:-1]
                            ),
                            1
                        )

                key = str(day_ago)[:10]
                self.site_views_info[key] = data
            else:
                log.info(f"No site visits for {model} {self.name}")
        else:
            log.warning(
                f"Failed getting site visits for {model} {self.name} "
                f"({res.status_code})")

        return self.site_views_info

    @property
    def get_youtube_stats(self):
        """ Youtube statistic (subscriberCount, viewCount). """
        stats = []
        if self.youtube_info.get('updated'):
            history = self.youtube_info.get('history', {})
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
    def get_youtube_trends(self):
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

    @property
    def get_twitter_stats(self):
        """ Twitter statistic (followers_count). """
        stats = []
        if self.twitter_info.get('updated'):
            history = self.twitter_info.get('history', {})
            last_update = self.twitter_info['updated']
            history[last_update] = {
                'followers_count': self.twitter_info.get('followers_count',
                                                         '0'),
            }

            dates = sorted(history.keys(), reverse=True)
            for d in dates:
                stats.append([d[:10], [
                    int(history[d]['followers_count']),
                ]])

        return stats

    @property
    def get_twitter_trends(self):
        """ Twitter weekly statistic (followers_count). """
        stats = []
        if self.twitter_info.get('history'):
            history = self.twitter_info['history']
            last_update = self.twitter_info['updated']
            history[last_update] = {
                'followers_count': self.twitter_info.get('followers_count',
                                                         '0'),
            }

            dates = sorted(history.keys(), reverse=True)
            for i, d in enumerate(dates[:-1]):
                stats.append([d[:10], [
                    int(history[d]['followers_count']) - int(
                        history[dates[i + 1]]['followers_count']),
                ]])

        return stats

    @property
    def get_trend_info(self):
        """ Get Youtube and Twitter trend info. """
        info = {
            'twitter_stats': self.get_twitter_stats,
            'twitter_trend': 0,
            'twitter_trend_date': False,
            'youtube_stats': self.get_youtube_stats,
            'youtube_trend': 0,
            'youtube_trend_date': False,
        }

        if len(info['twitter_stats']) > 1 and \
                info['twitter_stats'][1][1][0] != 0:
            info['twitter_trend_date'] = info['twitter_stats'][1][0]
            info['twitter_trend'] = round(
                (info['twitter_stats'][0][1][0] -
                 info['twitter_stats'][1][1][0]) /
                info['twitter_stats'][1][1][0] * 100,
                1
            )

        if len(info['youtube_stats']) > 1 and \
                info['youtube_stats'][1][1][0] != 0:
            info['youtube_trend_date'] = info['youtube_stats'][1][0]
            info['youtube_trend'] = round(
                (info['youtube_stats'][0][1][0] -
                 info['youtube_stats'][1][1][0]) /
                info['youtube_stats'][1][1][0] * 100,
                1
            )

        return info

    @property
    def get_wiki_stats(self):
        """ Wiki statistic (visits). """
        stats = []
        if self.wiki_views_info:
            dates = sorted(self.wiki_views_info.keys(), reverse=True)
            for d in dates:
                stats.append([d[:10], [int(self.wiki_views_info[d])]])

        return stats

    @property
    def get_wiki_trends(self):
        """ Wiki weekly statistic (visits). """
        trends = []
        if self.wiki_views_info:
            dates = sorted(self.wiki_views_info.keys(), reverse=True)
            for i, d in enumerate(dates[:-1]):
                trends.append([d[:10], [
                    int(self.wiki_views_info[d]) - int(
                        self.wiki_views_info[dates[i + 1]]),
                ]])

        return trends

    @property
    def get_awis_stats(self):
        """ Awis site visits. """
        stats = []
        if self.site_views_info:
            dates = sorted(self.site_views_info.keys(), reverse=True)
            top_5 = sorted(self.site_views_info[dates[-1]].items(),
                           key=operator.itemgetter(1), reverse=True)[1:6]
            countries = [country[0] for country in top_5]
            countries = {
                country: COUNTRIES[country]
                for country in countries
            }

            for d in dates:
                _stats = {'total': self.site_views_info[d]['total']}
                for code, name in countries.items():
                    _stats[name] = self.site_views_info[d][code]

                stats.append([d[:10], _stats])

        return stats


class League(models.Model, ModelMixin):
    wiki = models.URLField(unique=True)
    name = models.CharField(max_length=255, blank=True, db_index=True)
    photo = models.URLField(
        default=settings.NO_AVATAR_IMAGE,
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
    wiki_views_info = JSONField(default=dict, blank=True)
    site_views_info = JSONField(default=dict, blank=True)
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

        if not self.youtube_info.get('updated'):
            # Try to get youtube info.
            self.get_youtube_info()

        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)

        if not self.twitter_info.get('updated'):
            # Try to get twitter info.
            self.get_twitter_info()

    def __str__(self):
        return self.name


class Team(models.Model, ModelMixin):
    wiki = models.URLField(unique=True)
    name = models.CharField(max_length=255, blank=True, db_index=True)
    hashtag = models.CharField(max_length=32, blank=True)
    photo = models.URLField(
        default=settings.NO_AVATAR_IMAGE,
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
    wiki_views_info = JSONField(default=dict, blank=True)
    site_views_info = JSONField(default=dict, blank=True)
    stock_info = JSONField(default=dict, blank=True)
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
        site = urllib.parse.urlparse(self.wiki)
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
                geo_data = self.geocode(address)

                if geo_data['results']:
                    self.longitude = geo_data['results'][0]['geometry'][
                        'location']['lng']
                    self.latitude = geo_data['results'][0]['geometry'][
                        'location']['lat']

    def get_stock_info(self):
        """ Get stock info. """
        model = self.__class__.__name__

        log.info(f"Get stock info for {model} {self.name}")

        symbol = self.stock_info.get('symbol')
        if symbol:
            url = (
                "https://www.alphavantage.co/query"
                "?function=TIME_SERIES_DAILY"
                f"&apikey={settings.ALPHAVANTAGE_API_KEY}"
                f"&symbol={symbol}"
            )
            res = requests.get(url)
            if res.status_code == 200:
                stock_info = res.json()
                if stock_info and stock_info.get('Time Series (Daily)'):
                    for key, val in stock_info['Time Series (Daily)'].items():
                        self.stock_info[key] = val['4. close']

        return self.stock_info

    @property
    def get_stock_stats(self):
        """ Stock price. """
        stats = []
        self.stock_info.pop('symbol', None)
        dates = sorted(self.stock_info.keys(), reverse=True)

        for d in dates:
            stats.append([d, [float(self.stock_info[d])]])

        return stats

    @property
    def get_stock_trends(self):
        """ Stock price trends. """
        stats = []
        self.stock_info.pop('symbol', None)

        dates = sorted(self.stock_info.keys(), reverse=True)
        for i, d in enumerate(dates[:-1]):
            stats.append([d, [
                float(self.stock_info[d]) - float(
                    self.stock_info[dates[i + 1]]),
            ]])

        return stats

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.name:
            # If name isn't set - send request to Wiki to get additional info.
            self.get_data_from_wiki()

        # Get team location (latitude and longitude).
        if not self.latitude or not self.longitude:
            self.get_location()

        if not self.youtube_info.get('updated'):
            # Try to get youtube info.
            self.get_youtube_info()

        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)

        if not self.twitter_info.get('updated'):
            # Try to get twitter info.
            self.get_twitter_info()

    def __str__(self):
        return self.name


class Athlete(models.Model, ModelMixin):
    """ Athlete model. """
    wiki = models.URLField(unique=True)
    name = models.CharField(max_length=255, blank=True, db_index=True)
    photo = models.URLField(
        default=settings.NO_AVATAR_IMAGE,
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
    team = models.CharField(max_length=255, null=True, blank=True,
                            db_index=True)
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
    wiki_views_info = JSONField(default=dict, blank=True)
    site_views_info = JSONField(default=dict, blank=True)
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
                geo_data = self.geocode(address)

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

        if not self.youtube_info.get('updated'):
            # Try to get youtube info.
            self.get_youtube_info()

        super().save(force_insert=force_insert, force_update=force_update,
                     using=using, update_fields=update_fields)

        if not self.twitter_info.get('updated'):
            # Try to get amount od followers from twitter.
            self.get_twitter_info()

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


class Profile(models.Model):
    """ Profile model. """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='profile',
        on_delete=models.CASCADE
    )
    timezone = models.CharField(
        max_length=64,
        default='UTC'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        default='/avatars/no-avatar.png'
    )
    followed_athletes = models.ManyToManyField(
        Athlete,
        related_name='followers',
        blank=True
    )
    followed_teams = models.ManyToManyField(
        Team,
        related_name='followers',
        blank=True
    )
    followed_leagues = models.ManyToManyField(
        League,
        related_name='followers',
        blank=True
    )

    @property
    def name(self):
        if self.user.first_name:
            return f"{self.user.first_name} {self.user.last_name}"

        return self.user.username

    def __str__(self):
        return self.name
