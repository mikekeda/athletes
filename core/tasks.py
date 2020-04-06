import datetime
import logging
import urllib.parse

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.db.utils import IntegrityError
from django.template.loader import render_to_string
from django.utils import timezone
from requests_oauthlib import OAuth1

from core.celery import app
from core.constans import COUNTRIES
from core.models import Athlete, League, Team, Profile, TeamArticle

User = get_user_model()
log = logging.getLogger('athletes')

auth = OAuth1(
    settings.TWITTER_APP_KEY,
    settings.TWITTER_APP_SECRET,
    settings.TWITTER_OAUTH_TOKEN,
    settings.TWITTER_OAUTH_TOKEN_SECRET
)


def validate_link_and_create_athlete(link, site, data):
    """ Validate the link and create an athlete. """
    # If link has a space - it's player name.
    if link and link.string and len(link.string.split()) > 1:
        if link['href'][:4] != 'http':
            full_link = site + link['href']
        else:
            full_link = link['href']
        # Asynchronously add an athlete.
        if create_athlete_task(full_link, data):
            return full_link, True

        return full_link, False

    return None, False


def create_athlete_task(wiki, data):
    """ Task to crawl athletes from wiki team page. """
    athlete = Athlete.objects.filter(wiki=wiki).first()
    data = {key: val for key, val in data.items() if val}  # remove empty vals

    try:
        if not athlete:
            # Create an athlete.
            Athlete.objects.create(wiki=wiki, **data)
        else:
            # Update an athlete.
            for field in data:
                if not getattr(athlete, field):
                    setattr(athlete, field, data[field])
            athlete.save()
        return True
    except IntegrityError as e:
        log.warning("%s: Skip athlete for %s", repr(e), wiki)
        return False


@app.task
def parse_team(cleaned_data, skip_errors=False):
    wiki_url = cleaned_data.get('wiki', '')
    log.info("parsing team %s", wiki_url)
    site = urllib.parse.urlparse(wiki_url)
    site = f'{site.scheme}://{site.hostname}'
    html = requests.get(wiki_url)
    soup = BeautifulSoup(html.content, 'html.parser')
    cleaned_data['name'] = soup.title.string.split(' - Wikipedia')[0]

    html_ids = (
        "#Current_squad",
        "#Current_roster",
        "#Roster",
        "#First-team_squad",
        "#First_team_squad",
        "#Team_squad",
        "#Squad",
        "#Players",
        "#Current_Squad",
        "#Current_roster_and_coaching_staff",
        "#First_Team_Squad",
        "#Current_squad[11]",
        "#Current_players",
        "#Current_first_team_squad",
        "#Current_roster_and_Baseball_Hall_of_Fame",
        "#Team_roster",
        "#Team_roster_2018",
        "#2018_squad",
        "#Current_playing_squad",
        "#Playing_squad",
        "#Current_playing_list_and_coaches",
        "#Current_playing_lists",
        "#Team_Roster",
    )
    table = None

    for html_id in html_ids:
        title = soup.select(html_id)
        if not title:
            continue

        if cleaned_data.get('category') == "Handball":
            # Wiki pages for Handball category have table wrapped in div.
            table = title[0].parent.find_next_sibling("div")
            if table:
                table = table.select_one("table")
        else:
            table = title[0].parent.find_next_sibling("table")

        if table:
            break

    if skip_errors and not table:
        return

    team, _ = Team.objects.get_or_create(**cleaned_data)
    team.get_data_from_wiki(soup)
    if cleaned_data.get('league__pk'):
        team.league = League.objects.filter(pk=cleaned_data.pop(
            'league__pk')).first()
    team.save()

    cleaned_data['team'] = cleaned_data.pop('name', '')
    cleaned_data['team_model'] = team
    cleaned_data.pop('wiki', '')
    result = {'skipped': [], 'parsed': []}

    if cleaned_data.get('category') in ("American Football", "Baseball"):
        links = table.select("td > ul > li > a")

        for link in links:
            full_link, status = validate_link_and_create_athlete(
                link, site, cleaned_data
            )
            result[['skipped', 'parsed'][status]].append(full_link)
    elif cleaned_data.get('category') == "Ice Hockey":
        links = table.select("tr > td span.vcard a")

        for link in links:
            full_link, status = validate_link_and_create_athlete(
                link, site, cleaned_data
            )
            result[['skipped', 'parsed'][status]].append(full_link)
    elif cleaned_data.get('category') == "Cycling":
        links = table.select("tr > td span a")

        for link in links:
            full_link, status = validate_link_and_create_athlete(
                link, site, cleaned_data
            )
            result[['skipped', 'parsed'][status]].append(full_link)
    elif cleaned_data.get('category') == "Rugby":
        links = table.select("tr > td span.fn > a"
                             ) or table.select("tr > td ul > li a")

        for link in links:
            full_link, status = validate_link_and_create_athlete(
                link, site, cleaned_data
            )
            result[['skipped', 'parsed'][status]].append(full_link)
    elif cleaned_data.get('category') == "Australian Football":
        links = table.select("td > ul > li  a")

        for link in links:
            full_link, status = validate_link_and_create_athlete(
                link, site, cleaned_data
            )
            result[['skipped', 'parsed'][status]].append(full_link)
    elif cleaned_data.get('category') == "Cricket":
        links = table.select("tr > td:nth-of-type(2) > a")

        for link in links:
            full_link, status = validate_link_and_create_athlete(
                link, site, cleaned_data
            )
            result[['skipped', 'parsed'][status]].append(full_link)
    elif cleaned_data.get('category') == "Handball":
        links = table.select("td > ul > li  > a")

        for link in links:
            full_link, status = validate_link_and_create_athlete(
                link, site, cleaned_data
            )
            result[['skipped', 'parsed'][status]].append(full_link)
    else:
        # Default parsing.
        # Go through all table rows.
        for row in table.find_all("tr"):
            td = row.find_all(recursive=False)
            if len(td) > 3:
                for i in (2, 3):  # try to find players in 2th or 3th
                    link = td[i].find("a", recursive=False)
                    if not link:
                        # Sometimes a is wrapped with span.
                        link = td[i].find("span", recursive=False)
                        if link:
                            link = link.find("a", recursive=False)

                    if not link:
                        link = td[i].select_one("span.vcard a")

                    if link and link.string in ["United States", "South Korea", "North Korea", "Ivory Coast"
                                                ] + list(COUNTRIES.values()):
                        continue  # it's not a athlete

                    full_link, status = validate_link_and_create_athlete(
                        link, site, cleaned_data
                    )
                    result[['skipped', 'parsed'][status]].append(
                        full_link)

    result['skipped'] = [link for link in result['skipped'] if link]

    return result


@app.task
def weekly_athletes_youtube_update():
    """ Update youtube info for Athlete weekly. """
    aids = sorted(Athlete.objects.filter(~Q(youtube_info={})).values_list(
        'id', flat=True))

    for aid in aids:
        athlete = Athlete.objects.get(id=aid)
        athlete.get_youtube_info()
        super(Athlete, athlete).save()


@app.task
def weekly_youtube_update():
    """ Update youtube info for League and Team weekly. """
    for cls in (League, Team):
        ids = sorted(cls.objects.filter(~Q(youtube_info={})).values_list('id', flat=True))

        for _id in ids:
            obj = cls.objects.get(id=_id)
            obj.get_youtube_info()
            super(cls, obj).save()


@app.task
def weekly_athletes_twitter_update():
    """ Update twitter info for Athlete weekly. """
    ids = sorted(Athlete.objects.values_list('id', flat=True))

    for _id in ids:
        athlete = Athlete.objects.get(id=_id)
        athlete.get_twitter_info()


@app.task
def weekly_trends_notifications(teams=False):
    """ Send email to admins with twitter and youtube trends. """
    lim = 10  # top 10

    if teams:
        subject = "Weekly trends teams"
    else:
        subject = "Weekly trends athletes"

    if teams:
        ids = sorted(Team.objects.values_list('id', flat=True))
    else:
        ids = sorted(Athlete.objects.values_list('id', flat=True))

    twitter_trends = {}
    youtube_subscribers_trends = {}
    youtube_views_trends = {}

    for _id in ids:
        if teams:
            obj = Team.objects.get(id=_id)
        else:
            obj = Athlete.objects.get(id=_id)

        if obj.twitter_info and obj.twitter_info.get('history'):
            diff = obj.get_twitter_trends[0][1][0]
            if len(twitter_trends) < lim or diff > min(twitter_trends.keys()):
                if len(twitter_trends) >= lim:
                    twitter_trends.pop(min(twitter_trends.keys()))

                obj.new_followers = diff  # added new followers
                twitter_trends[diff] = obj

        if obj.youtube_info and obj.youtube_info.get('history'):
            diff = obj.get_youtube_trends[0][1][0]
            if len(youtube_subscribers_trends) < lim or diff > min(
                    youtube_subscribers_trends.keys()):
                if len(youtube_subscribers_trends) >= lim:
                    youtube_subscribers_trends.pop(min(
                        youtube_subscribers_trends.keys()))

                obj.new_subscribers = diff  # added new subscribers
                youtube_subscribers_trends[diff] = obj

            diff = obj.get_youtube_trends[0][1][1]
            if len(youtube_views_trends) < lim or diff > min(
                    youtube_views_trends.keys()):
                if len(youtube_views_trends) >= lim:
                    youtube_views_trends.pop(min(youtube_views_trends.keys()))

                obj.new_views = diff  # added new views
                youtube_views_trends[diff] = obj

    # Sort items by new followers.
    twitter_trends = {
        k: twitter_trends[k]
        for k in sorted(twitter_trends.keys(), reverse=True)
    }

    # Sort items by new subscribers.
    youtube_subscribers_trends = {
        k: youtube_subscribers_trends[k]
        for k in sorted(youtube_subscribers_trends.keys(), reverse=True)
    }

    # Sort items by new views.
    youtube_views_trends = {
        k: youtube_views_trends[k]
        for k in sorted(youtube_views_trends.keys(), reverse=True)
    }

    # Send notification to staff users.
    profiles = Profile.objects.filter(user__is_staff=True)

    for profile in profiles:
        if teams:
            template = '_trends-teams-email.html'
        else:
            template = '_trends-athletes-email.html'

        html_content = render_to_string(template, {
            'subject': subject,
            'twitter_trends': twitter_trends.values(),
            'youtube_subscribers_trends': youtube_subscribers_trends.values(),
            'youtube_views_trends': youtube_views_trends.values(),
        })

        msg = EmailMultiAlternatives(
            subject,
            "Visit our site to check the updates",
            f"Athletes <notify@{settings.MAILGUN_SERVER_NAME}>",
            [f"{profile.name} <{profile.user.email}>"],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()


@app.task
def weekly_twitter_update():
    """ Update twitter info for League and Team weekly. """
    for cls in (League, Team):
        ids = sorted(cls.objects.values_list('id', flat=True))

        for _id in ids:
            obj = cls.objects.get(id=_id)
            obj.get_twitter_info()


@app.task
def weekly_wiki_views_update():
    """ Update wiki visits info for League, Team and Athlete weekly. """
    for cls in (League, Team, Athlete):
        ids = sorted(cls.objects.values_list('id', flat=True))

        for _id in ids:
            obj = cls.objects.get(id=_id)
            obj.get_wiki_views_info()
            super(cls, obj).save()


@app.task
def weekly_stock_update():
    """ Update stock info for Teams weekly. """
    ids = sorted(Team.objects.filter(~Q(stock_info={})).values_list(
        'id', flat=True))

    for _id in ids:
        obj = Team.objects.get(id=_id)
        obj.get_stock_info()
        super(Team, obj).save()


@app.task
def weekly_awis_update():
    """ Update awis statistic for League and related Teams weekly. """
    ids = sorted(League.objects.values_list('id', flat=True))

    for _id in ids:
        league = League.objects.prefetch_related('teams').get(id=_id)
        league.get_awis_info()
        super(League, league).save()

        for team in league.teams.all():
            team.get_awis_info()
            super(Team, team).save()


@app.task
def yearly_duedil_update():
    """ Update company info for Teams yearly. """
    ids = sorted(Team.objects.filter(~Q(company_info={})).values_list(
        'id', flat=True))

    for _id in ids:
        team = Team.objects.get(id=_id)
        team.get_company_info()
        super(Team, team).save()


@app.task
def daily_teams_news_update():
    """ Get articles related to specific teams. """
    # Get famous teams (with website and twitter, we have 876 teams on prod).
    ids = sorted(Team.objects.exclude(
        additional_info__Website__isnull=True
    ).filter(~Q(twitter_info={})).values_list('id', flat=True))

    for _id in ids:
        team = Team.objects.get(id=_id)
        TeamArticle.get_articles(team)


@app.task
def every_minute_twitter_update():
    """ Update twitter info with respect to api limitation. """
    # pattern is 'twitter_update_cls_id'
    # due to twitter limits we can send only 60 requests per minute
    keys = cache.keys('twitter_update_*')[:60]

    for key in keys:
        cache.delete(key)  # first delete the key

        historical_keys = ('followers_count',)

        cls_name, pk = key[len('twitter_update_'):].split('_')
        cls = {
            'Athlete': Athlete,
            'League': League,
            'Team': Team
        }.get(cls_name)

        obj = cls.objects.get(id=pk)
        history = obj.twitter_info.get('history', {})
        now = datetime.datetime.now()
        if obj.twitter_info:
            week_ago = str(now - datetime.timedelta(weeks=1))
            last_update = obj.twitter_info.get('updated', week_ago)

            history[last_update] = {}
            for field in historical_keys:
                history[last_update][field] = obj.twitter_info.get(field, 0)

        if obj.twitter_info.get('screen_name'):
            log.info("Update info from Twitter for %s %s", cls_name, obj.name)
            screen_name = obj.twitter_info['screen_name']

            url = f"https://api.twitter.com/1.1/users/show.json?screen_name={screen_name}"

        else:
            log.info("Get info from Twitter for %s %s", cls_name, obj.name)
            urlencoded_name = urllib.parse.quote_plus(obj.name)

            url = (
                "https://api.twitter.com/1.1/users/search.json"
                "?count=1"  # we need only 1
                f"&q={urlencoded_name} {obj.category}"
            )

        res = requests.get(url, auth=auth)
        if res.status_code == 200:
            twitter_info = res.json()
            if twitter_info:
                if isinstance(twitter_info, list):
                    twitter_info = twitter_info[0]

                obj.twitter = twitter_info['followers_count']
                obj.twitter_info = twitter_info
                obj.twitter_info['updated'] = str(now)
                obj.twitter_info['history'] = history
            else:
                log.info("No twitter info for %s %s", cls_name, obj.name)
        else:
            log.warning("Failed getting twitter info for %s %s (%s)", cls_name, obj.name, res.status_code)

        super(cls, obj).save()


@app.task
def daily_update_notifications():
    """ Send email to users about recent updates. """
    day_ago = timezone.now() - timezone.timedelta(days=1)
    subject = "Your followed Athletes, Teams, Leagues were recently updated"
    today = datetime.datetime.today()

    ids = Profile.objects.exclude(
        followed_athletes=None,
        followed_teams=None,
        followed_leagues=None
    ).values_list('id', flat=True)

    for pk in ids:
        profile = Profile.objects.get(pk=pk)

        if any((
                profile.notification_frequency == 'never',
                profile.notification_frequency == 'monthly' and today.day != 1,
                profile.notification_frequency == 'weekly' and today.weekday() != 1
        )):
            continue

        updates = {
            'athletes': profile.followed_athletes.filter(updated__gte=day_ago),
            'teams': profile.followed_teams.filter(updated__gte=day_ago),
            'leagues': profile.followed_leagues.filter(updated__gte=day_ago),
        }

        # If no recent updates - continue.
        if not any([updates['athletes'], updates['teams'],
                    updates['leagues']]):
            continue

        html_content = render_to_string('_alert-email.html', {
            'subject': subject,
            'athletes': updates['athletes'],
            'teams': updates['teams'],
            'leagues': updates['leagues'],
        })

        msg = EmailMultiAlternatives(
            subject,
            "Visit our site to check the updates",
            f"Athletes <notify@{settings.MAILGUN_SERVER_NAME}>",
            [f"{profile.name} <{profile.user.email}>"],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
