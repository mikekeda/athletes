from bs4 import BeautifulSoup
import datetime
import json
import logging
import requests
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core import serializers
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.views import View
from django.utils.decorators import method_decorator

from core.forms import TeamForm
from core.models import COUNTRIES, Athlete, Team
from core.tasks import create_athlete_task


log = logging.getLogger('athletes')


def validate_link_and_create_athlete(link, site, data):
    """ Validate the link and create an athlete. """
    # If link has a space - it's player name.
    if link and link.string and len(link.string.split()) > 1:
        if link['href'][:4] != 'http':
            full_link = site + link['href']
        else:
            full_link = link['href']
        # Asynchronously add an athlete.
        create_athlete_task(full_link, data)


def _serialize_qs(qs):
    ages = {}  # serialize removes age property, so we need to add it again

    for obj in qs:
        ages[obj.id] = obj.age

        for field in Athlete._meta.get_fields():
            try:
                setattr(obj, field.name,
                        getattr(obj, f'get_{field.name}_display')())
            except AttributeError:
                pass

    data = json.loads(serializers.serialize('json', qs))
    data = [{**obj['fields'], 'age': ages.get(obj['pk'], '')} for obj in data]

    return data


def _process_datatables_params(querydict: dict) -> tuple:
    """ Process datatables params. """
    search = querydict.get('search[value]', '')

    try:
        start = int(querydict.get('start', 0))
    except ValueError:
        start = 0

    try:
        length = int(querydict.get('length', 10))
    except ValueError:
        length = 10

    try:
        draw = int(querydict.get('draw', 1))
    except ValueError:
        draw = 1

    col_data = []
    filters = {}
    cnt = 0
    while f'columns[{cnt}][name]' in querydict:
        searchable = querydict.get(f'columns[{cnt}][searchable]') == 'true'
        orderable = querydict.get(f'columns[{cnt}][orderable]') == 'true'
        key = querydict.get(f'columns[{cnt}][data]')
        search_value = querydict.get(f'columns[{cnt}][search][value]')

        col_data.append({
            'name': querydict.get(f'columns[{cnt}][name]'),
            'data': key,
            'searchable': searchable,
            'orderable': orderable,
            'search.value': search_value,
            'search.regex': querydict.get(f'columns[{cnt}][search][regex]'),
        })

        if search_value:
            filters[key] = search_value

        cnt += 1

    order = []
    cnt = 0
    while f'order[{cnt}][column]' in querydict:
        sortcol = int(querydict.get(f'order[{cnt}][column]'))
        sort_dir = querydict.get(f'order[{cnt}][dir]')
        sort_key = '-' if sort_dir == 'desc' else ''
        order.append(sort_key + col_data[sortcol]['data'])

        cnt += 1

    return draw, start, length, order, search, filters


@login_required
def athletes_api(request):
    """ Return filtered/sorted/paginated list of athletes for datatables. """
    draw, start, length, order, search, filters = _process_datatables_params(
        request.GET)

    # Count all rows.
    total = Athlete.objects.count()

    # Form queryset.
    qs = Athlete.objects

    if filters:
        for field, val in filters.items():
            if field == 'age':  # we don't have age field (it's property)
                field = 'birthday'  # we will use birthday in query

            model_field = Athlete._meta.get_field(field)

            if field == 'birthday':
                val = val.split('-')

                for i, _ in enumerate(val):
                    today = datetime.date.today()
                    val[i] = datetime.date(today.year - int(val[i]),
                                           today.month, today.day)

                qs = qs.filter(
                    **{f'{field}__gte': val[1], f'{field}__lte': val[0]}
                )
            elif field in ('instagram', 'twiter'):
                val = val.split('-')
                qs = qs.filter(
                    **{f'{field}__gte': val[0], f'{field}__lte': val[1]}
                )
            elif field in ('domestic_market', 'location_market'):
                country_val = [
                    code
                    for code, name in COUNTRIES.items()
                    if val.lower() in name.lower()
                ]
                qs = qs.filter(**{f'{field}__in': country_val})
            elif model_field.choices:
                qs = qs.filter(**{f'{field}__in': val.split(',')})
            elif model_field.get_internal_type() == 'BooleanField':
                qs = qs.filter(**{f'{field}': val == 'true'})
            else:
                qs = qs.filter(**{f'{field}__icontains': val})

    if search:
        # Smart search by name, domestic_market, gender,
        # location_market, team, category fields.
        country_val = [
            code
            for code, name in COUNTRIES.items()
            if search.lower() in name.lower()
        ]

        qs = qs.filter(
            Q(name__icontains=search) |
            Q(domestic_market__in=country_val) |
            Q(gender__icontains=search) |
            Q(location_market__in=country_val) |
            Q(team__icontains=search) |
            Q(category__icontains=search)
        )

    # Count filtered rows.
    if filters or search:
        filtered = qs.count()
    else:
        filtered = total  # no need to count filtered rows

    qs = qs.order_by(*order)

    # Pagination.
    qs = qs[start:start + length]

    return JsonResponse(
        {
            "draw": draw,
            "recordsTotal": total,
            "recordsFiltered": filtered,
            "data": _serialize_qs(qs)
        }
    )


@login_required
def crm_page(request):
    """ CRM page. """
    model = Athlete._meta

    return render(request, 'crm.html', {
        'gender_choices': model.get_field('gender').choices,
        'category_choices': model.get_field('category').choices,
        'optimal_campaign_choices': model.get_field('optimal_campaign').choices
    })


def about_page(request):
    """ About page. """
    return render(request, 'about.html')


@method_decorator(staff_member_required, name='dispatch')
class ParseTeamView(View):
    """ Crawling athletes from team wiki page. """

    # noinspection PyMethodMayBeStatic
    def get(self, request):
        """ Get form. """
        form = TeamForm()
        return render(request, 'wiki-team-form.html', {'form': form})

    # noinspection PyMethodMayBeStatic
    def post(self, request):
        """ Form submit. """
        form = TeamForm(data=request.POST)
        if form.is_valid():
            wiki_url = form.cleaned_data.get('wiki', '')
            log.info(f"parsing team {wiki_url}")
            site = urlparse(wiki_url)
            site = f'{site.scheme}://{site.hostname}'
            html = requests.get(wiki_url)
            soup = BeautifulSoup(html.content, 'html.parser')
            title = soup.select(
                "#Current_squad") or soup.select(
                "#Current_roster") or soup.select(
                "#Roster") or soup.select(
                "#First-team_squad") or soup.select(
                "#First_team_squad") or soup.select(
                "#Team_squad") or soup.select(
                "#Squad")
            form.cleaned_data['team'] = soup.title.string.split(
                ' - Wikipedia')[0]
            table = title[0].parent.find_next_sibling("table")

            team, _ = Team.objects.get_or_create(**form.cleaned_data)
            team.get_data_from_wiki(soup)
            team.save()

            form.cleaned_data['team_model'] = team
            form.cleaned_data.pop('wiki', '')

            if form.cleaned_data.get('category') == "American Football":
                links = table.select("td > ul > li > a")

                for link in links:
                    validate_link_and_create_athlete(link, site,
                                                     form.cleaned_data)

            if form.cleaned_data.get('category') == "Ice Hockey":
                links = table.select("tr > td span.vcard a")

                for link in links:
                    validate_link_and_create_athlete(link, site,
                                                     form.cleaned_data)
            else:
                # Default parsing.
                # Go through all table rows.
                for row in table.findAll("tr"):
                    td = row.find_all(recursive=False)
                    if len(td) > 3:
                        for i in (2, 3):  # try to find players in 2th or 3th
                            link = td[i].find("a", recursive=False)
                            if not link:
                                # Sometimes a is wrapped with span.
                                link = td[i].find("span", recursive=False)
                                if link:
                                    link = link.find("a", recursive=False)

                            validate_link_and_create_athlete(
                                link, site, form.cleaned_data)

            form = TeamForm(initial=form.cleaned_data)

        return render(request, 'wiki-team-form.html', {'form': form})


def login_page(request):
    """ User login page. """
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(reverse('core:crm'))

    return render(request, 'login.html', {'form': form})


@login_required
def logout_page(request):
    """ User logout callback. """
    logout(request)
    return redirect(reverse('core:login'))
