import json

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core import serializers
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse

from core.models import Athlete


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
            model_field = Athlete._meta.get_field(field)

            if model_field.choices:
                qs = qs.filter(**{f'{field}__in': val.split(',')})
            elif model_field.get_internal_type() == 'BooleanField':
                qs = qs.filter(**{f'{field}': val == 'true'})
            else:
                qs = qs.filter(**{f'{field}__icontains': val})

    if search:
        # Smart search by name, nationality_and_domestic_market, gender,
        # location_market, team, category fields.
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(nationality_and_domestic_market__icontains=search) |
            Q(gender__icontains=search) |
            Q(location_market__icontains=search) |
            Q(team__icontains=search) |
            Q(category__icontains=search)
        )

    qs = qs.order_by(*order)

    # Count filtered rows.
    filtered = qs.count()

    # Pagination.
    qs = qs[start:start + length]

    data = json.loads(serializers.serialize('json', qs))
    data = [obj['fields'] for obj in data]

    return JsonResponse(
        {
            "draw": draw,
            "recordsTotal": total,
            "recordsFiltered": filtered,
            "data": data
        }
    )


@login_required
def home_page(request):
    """ Home page. """
    return render(request, 'home.html')


def about_page(request):
    """ About page. """
    return render(request, 'about.html')


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
