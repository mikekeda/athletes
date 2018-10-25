import datetime
import logging
import random
from collections import Counter
from urllib.parse import urlparse, quote_plus

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, Sum
from django.db.models.expressions import RawSQL
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View

from core.constans import CATEGORIES, MAP_COUNTRIES, COUNTRIES
from core.forms import TeamForm, LeagueForm, AthletesListForm
from core.models import (Athlete, League, Team, AthletesList, TeamsList,
                         LeaguesList, Profile)
from core.tasks import parse_team

log = logging.getLogger('athletes')


@method_decorator(staff_member_required, name='dispatch')
class ParseTeamView(View):
    """ Crawling athletes from team wiki page. """

    # noinspection PyMethodMayBeStatic
    def get(self, request):
        """ Get form. """
        form = TeamForm()
        return render(request, 'wiki-team-form.html',
                      {'form': form, 'action': reverse('core:team_parse')})

    # noinspection PyMethodMayBeStatic
    def post(self, request):
        """ Form submit. """
        form = TeamForm(data=request.POST)
        if form.is_valid():
            result = parse_team(form.cleaned_data)

            form = TeamForm(initial=form.cleaned_data)

            return render(request, 'wiki-team-form.html',
                          {'form': form, 'parsed': result['parsed'],
                           'skipped': result['skipped'],
                           'action': reverse('core:team_parse')})

        return render(request, 'wiki-team-form.html',
                      {'form': form, 'action': reverse('core:team_parse')})


@method_decorator(staff_member_required, name='dispatch')
class ParseLeagueView(View):
    """ Crawling athletes from team list wiki page. """

    # noinspection PyMethodMayBeStatic
    def get(self, request):
        """ Get form. """
        form = LeagueForm()
        return render(request, 'wiki-team-form.html',
                      {'form': form, 'action': reverse('core:league_parse')})

    # noinspection PyMethodMayBeStatic
    def post(self, request):
        """ Form submit. """
        form = LeagueForm(data=request.POST)

        if form.is_valid():
            selector = form.cleaned_data.pop('selector')

            league, _ = League.objects.get_or_create(**form.cleaned_data)

            wiki_url = form.cleaned_data.get('wiki')
            site = urlparse(wiki_url)
            site = f'{site.scheme}://{site.hostname}'
            log.info(f"parsing teams {wiki_url}")
            html = requests.get(wiki_url)
            soup = BeautifulSoup(html.content, 'html.parser')
            links = soup.select(selector)

            for link in links:
                if not link.get('href'):
                    continue

                if link['href'][:4] != 'http':
                    link['href'] = site + link['href']

                cleaned_data = form.cleaned_data.copy()
                cleaned_data['wiki'] = link['href']
                cleaned_data['league__pk'] = league.pk
                cleaned_data.pop('selector', '')
                parse_team.delay(cleaned_data, True)

            # Clean fields and add selector.
            form.cleaned_data['selector'] = selector
            for key in ('wiki', 'location_market'):
                form.cleaned_data.pop(key, '')
            form = LeagueForm(initial=form.cleaned_data)

        return render(request, 'wiki-team-form.html',
                      {'form': form, 'action': reverse('core:league_parse')})


@login_required
def crm_page(request):
    """ CRM page. """
    form = AthletesListForm()
    model = Athlete._meta
    athletes_lists = AthletesList.objects.filter(user=request.user).only(
        'pk', 'name')

    return render(request, 'crm.html', {
        'form': form,
        'athletes_lists': athletes_lists,
        'gender_choices': model.get_field('gender').choices,
        'category_choices': model.get_field('category').choices,
        'optimal_campaign_choices': model.get_field('optimal_campaign').choices
    })


def about_page(request):
    """ About page. """
    return render(request, 'about.html')


@login_required
def map_page(request):
    """ Map page. """
    category = request.GET.get('category', '').title()
    gender = request.GET.get('gender')

    qs = Athlete.objects
    if category in CATEGORIES:
        # Filter by category.
        qs = qs.filter(category=category)
    if gender:
        # Filter by category.
        qs = qs.filter(gender=gender)

    # Count how many athletes we have for each country.
    cont = qs.values('location_market').annotate(
        total=Count('location_market'))
    cont = {c['location_market']: c['total'] for c in cont}

    max_total = max(cont.values(), default=1)
    countries = MAP_COUNTRIES.copy()
    for country in countries:
        country['total'] = cont.get(country['id'], 0)

        # Calculate opacity for each country, more athletes - darker.
        # Min opacity = 0.1, max opacity = 1 (for country with max athletes)
        country['opacity'] = 0.9 * country['total'] / max_total + 0.1

    return render(request, 'map.html', {'countries': countries})


def terms_page(request):
    """ Terms of service page. """
    return render(request, 'terms.html')


@login_required
def athlete_page(request, slug):
    """ Athlete page. """
    slug = quote_plus(slug, safe='(,)')
    athlete = get_object_or_404(
        Athlete.objects.prefetch_related('athletes_lists'),
        wiki__endswith=slug
    )
    athletes_lists = AthletesList.objects.filter(user=request.user).only(
        'pk', 'name')
    subscribed = Profile.objects.filter(user=request.user,
                                        followed_athletes=athlete).exists()

    # Check if the athlete is in any list.
    for athletes_list in athletes_lists:
        athletes_list.selected = athletes_list in athlete.athletes_lists.all()

    return render(request, 'athlete.html', {
        'athlete': athlete,
        'athletes_lists': athletes_lists,
        'subscribed': subscribed,
    })


@login_required
def team_page(request, pk):
    """ Team page. """
    team = get_object_or_404(Team, pk=pk)
    athletes = Athlete.objects.filter(team_model=team).only('name', 'wiki')

    teams_lists = TeamsList.objects.filter(user=request.user).only(
        'pk', 'name')
    subscribed = Profile.objects.filter(user=request.user,
                                        followed_teams=team).exists()

    # Check if the athlete is in any list.
    for teams_list in teams_lists:
        teams_list.selected = teams_list in team.teams_lists.all()

    # Collect squad age statistic.
    counter = Counter()

    for athlete in athletes:
        counter[athlete.age] += 1

    total = sum(counter.values())
    counter = sorted(counter.items())

    age_dataset = {
        'datasets': [{
            'data': [c[1] for c in counter],
            'backgroundColor': [
                f'rgba(255, 0, 0, {(c[0] - 15) / 30})' for c in counter
            ]
        }],
        'labels': [
            f'{c[0]} ({round(c[1] * 100 / total, 1)}%)'
            for c in counter
        ]
    }

    # Collect squad domestic_market statistic.
    counter = Counter()

    for athlete in athletes:
        counter[athlete.get_domestic_market_display()] += 1

    total = sum(counter.values())
    counter = sorted(counter.items())

    domestic_market_dataset = {
        'datasets': [{
            'data': [c[1] for c in counter],
            'backgroundColor': [
                f'rgb({random.randint(0, 255)}, {random.randint(0, 255)}, '
                f'{random.randint(0, 255)})' for _ in counter
            ]
        }],
        'labels': [
            f'{c[0]} ({round(c[1] * 100 / total, 1)}%)'
            for c in counter
        ]
    }

    return render(request, 'team.html', {
        'team': team,
        'athletes': athletes,
        'teams_lists': teams_lists,
        'age_dataset': age_dataset,
        'domestic_market_dataset': domestic_market_dataset,
        'subscribed': subscribed,
    })


@login_required
def league_page(request, pk):
    """ League page. """
    league = get_object_or_404(League, pk=pk)
    teams = Team.objects.filter(league=league).only('name', 'wiki')

    league_lists = LeaguesList.objects.filter(user=request.user).only(
        'pk', 'name')
    subscribed = Profile.objects.filter(user=request.user,
                                        followed_leagues=league).exists()

    # Check if the athlete is in any list.
    for league_list in league_lists:
        league_list.selected = league_list in league.leagues_lists.all()

    return render(request, 'league.html', {
        'league': league,
        'teams': teams,
        'league_lists': league_lists,
        'subscribed': subscribed,
    })


@login_required
def country_page(request, code):
    """ Country page. """
    code = code.upper()
    name = COUNTRIES[code]

    window = RawSQL("to_timestamp(avg(extract(epoch from birthday)))", [])
    window.get_group_by_cols = lambda: []

    stats = Athlete.objects.filter(
        location_market=code
    ).values(
        'category',
    ).annotate(
        twitter=Sum('twitter'),
        athletes=Count('location_market'),
        birthday=window,
    )
    today = datetime.date.today()
    for row in stats:
        row['age'] = today.year - row['birthday'].year - (
                (today.month, today.day) < (
            row['birthday'].month, row['birthday'].day))

    return render(request, 'country.html', {'name': name, 'stats': stats})


def login_page(request):
    """ User login page. """
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            Profile.objects.get_or_create(user=user)
            return redirect(reverse('core:crm'))

    return render(request, 'login.html', {'form': form})


@login_required
def logout_page(request):
    """ User logout callback. """
    logout(request)
    return redirect(reverse('core:login'))
