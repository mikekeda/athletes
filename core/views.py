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
from django.db.models import Q, F, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.views import View
from django.utils.decorators import method_decorator

from core.constans import CATEGORIES, MAP_COUNTRIES
from core.forms import TeamForm, TeamsForm
from core.models import COUNTRIES, Athlete
from core.tasks import parse_team


log = logging.getLogger('athletes')


def _serialize_qs(qs):
    props = {}  # serialize removes properties, so we need to add them again

    for obj in qs:
        props[obj.id] = {'age': obj.age, 'market_export': obj.market_export}

        for field in Athlete._meta.get_fields():
            try:
                setattr(obj, field.name,
                        getattr(obj, f'get_{field.name}_display')())
            except AttributeError:
                pass

    data = json.loads(serializers.serialize('json', qs))
    data = [{**obj['fields'], **props.get(obj['pk'], {})} for obj in data]

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

        if col_data[sortcol]['data'] == 'age':
            sort_key = '' if sort_dir == 'desc' else '-'
            order.append(sort_key + 'birthday')
        else:
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
    qs = Athlete.objects.defer('additional_info', 'twitter_info')

    if filters:
        for field, val in filters.items():
            # Process filtering by properties.
            if field == 'market_export':
                if val == 'true':
                    qs = qs.exclude(domestic_market=F('location_market'))
                else:
                    qs = qs.filter(domestic_market=F('location_market'))
                continue

            elif field == 'age':
                val = val.split('-')

                for i, _ in enumerate(val):
                    today = datetime.date.today()
                    val[i] = datetime.date(today.year - int(val[i]),
                                           today.month, today.day)

                qs = qs.filter(birthday__gte=val[1], birthday__lte=val[0])
                continue

            model_field = Athlete._meta.get_field(field)

            if field in ('instagram', 'twitter'):
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


@login_required
def map_page(request):
    """ Map page. """
    category = request.GET.get('category', '').title()

    if category in CATEGORIES:
        # Filter by category.
        qs = Athlete.objects.filter(category=category)
    else:
        qs = Athlete.objects.all()

    # Count how many athletes we have for each country.
    cont = qs.values('location_market').annotate(
        total=Count('location_market'))
    cont = {c['location_market']: c['total'] for c in cont}

    max_total = max(cont.values(), default=1)
    countries = MAP_COUNTRIES.copy()
    for country in countries:
        # Calculate opacity for each country, more athletes - darker.
        # Min opacity = 0.1, max opacity = 1 (for country with max athletes)
        country['opacity'] = (0.9 * cont.get(country['id'], 0) / max_total
                              + 0.1)

    return render(request, 'map.html', {'countries': countries})


def terms(request):
    """ Terms of service page. """
    return render(request, 'terms.html')


@method_decorator(staff_member_required, name='dispatch')
class ParseTeamView(View):
    """ Crawling athletes from team wiki page. """

    # noinspection PyMethodMayBeStatic
    def get(self, request):
        """ Get form. """
        form = TeamForm()
        return render(request, 'wiki-team-form.html',
                      {'form': form, 'action': reverse('core:team')})

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
                           'action': reverse('core:team')})

        return render(request, 'wiki-team-form.html',
                      {'form': form, 'action': reverse('core:team')})


@method_decorator(staff_member_required, name='dispatch')
class ParseTeamsView(View):
    """ Crawling athletes from team list wiki page. """

    # noinspection PyMethodMayBeStatic
    def get(self, request):
        """ Get form. """
        form = TeamsForm()
        return render(request, 'wiki-team-form.html',
                      {'form': form, 'action': reverse('core:teams')})

    # noinspection PyMethodMayBeStatic
    def post(self, request):
        """ Form submit. """
        form = TeamsForm(data=request.POST)
        if form.is_valid():
            selector = form.cleaned_data.get('selector')
            wiki_url = form.cleaned_data.get('wiki')
            site = urlparse(wiki_url)
            site = f'{site.scheme}://{site.hostname}'
            log.info(f"parsing teams {wiki_url}")
            html = requests.get(wiki_url)
            soup = BeautifulSoup(html.content, 'html.parser')
            links = soup.select(selector)

            for link in links:
                if link['href'][:4] != 'http':
                    link['href'] = site + link['href']

                cleaned_data = form.cleaned_data.copy()
                cleaned_data['wiki'] = link['href']
                cleaned_data.pop('selector', '')
                parse_team.delay(cleaned_data, True)

            # Clean fields
            for key in ('wiki', 'location_market'):
                form.cleaned_data.pop(key, '')
            form = TeamsForm(initial=form.cleaned_data)

        return render(request, 'wiki-team-form.html',
                      {'form': form, 'action': reverse('core:teams')})


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
