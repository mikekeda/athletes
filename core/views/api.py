import csv
import datetime
import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import TrigramSimilarity
from django.core import serializers
from django.db.models import Case, CharField, F, Q, When
from django.db.models.functions import Greatest
from django.http import Http404, HttpResponse, JsonResponse, QueryDict
from django.shortcuts import get_object_or_404

from core.constans import CATEGORIES, COUNTRIES
from core.forms import AthletesListForm
from core.models import (
    Athlete,
    AthletesList,
    League,
    LeaguesList,
    Profile,
    Team,
    TeamsList,
)

log = logging.getLogger("athletes")


def _serialize_qs(qs):
    props = {}  # serialize removes properties, so we need to add them again

    for obj in qs:
        props[obj.id] = {
            "age": getattr(obj, "age", None),
            "market_export": getattr(obj, "market_export", None),
            "slug": getattr(obj, "slug", None),
            "twitter": obj.twitter_info.get("followers_count"),
            "_domestic_market": getattr(obj, "domestic_market", None),
            "_location_market": getattr(obj, "location_market", None),
        }
        if hasattr(obj, "league"):
            props[obj.id]["league"] = {
                "pk": getattr(obj.league, "pk", None),
                "name": getattr(obj.league, "name", None),
            }

        for field in Athlete._meta.get_fields():
            try:
                setattr(obj, field.name, getattr(obj, f"get_{field.name}_display")())
            except AttributeError:
                pass

    data = json.loads(serializers.serialize("json", qs))
    data = [
        {**obj["fields"], **props.get(obj["pk"], {}), "pk": obj["pk"]} for obj in data
    ]

    return data


def _process_datatables_params(querydict: dict) -> tuple:
    """Process datatables params."""
    search = querydict.get("search[value]", "")

    try:
        start = int(querydict.get("start", 0))
    except ValueError:
        start = 0

    try:
        length = int(querydict.get("length", 10))
    except ValueError:
        length = 10

    try:
        draw = int(querydict.get("draw", 1))
    except ValueError:
        draw = 1

    col_data = []
    filters = {}
    cnt = 0
    while f"columns[{cnt}][name]" in querydict:
        searchable = querydict.get(f"columns[{cnt}][searchable]") == "true"
        orderable = querydict.get(f"columns[{cnt}][orderable]") == "true"
        key = querydict.get(f"columns[{cnt}][data]")
        search_value = querydict.get(f"columns[{cnt}][search][value]")

        col_data.append(
            {
                "name": querydict.get(f"columns[{cnt}][name]"),
                "data": key,
                "searchable": searchable,
                "orderable": orderable,
                "search.value": search_value,
                "search.regex": querydict.get(f"columns[{cnt}][search][regex]"),
            }
        )

        if search_value:
            filters[key] = search_value

        cnt += 1

    order = []
    cnt = 0
    while f"order[{cnt}][column]" in querydict:
        try:
            sortcol = int(querydict.get(f"order[{cnt}][column]"))
        except ValueError:
            sortcol = 0

        sort_dir = querydict.get(f"order[{cnt}][dir]")

        if col_data[sortcol]["data"] == "age":
            sort_key = "" if sort_dir == "desc" else "-"
            order.append(sort_key + "birthday")
        else:
            sort_key = "-" if sort_dir == "desc" else ""
            order.append(sort_key + col_data[sortcol]["data"])

        cnt += 1

    return draw, start, length, order, search, filters


def _athletes_api(request):
    """Return filtered/sorted/paginated list of athletes for datatables."""
    draw, start, length, order, search, filters = _process_datatables_params(
        request.GET
    )

    # Count all rows.
    total = Athlete.objects.count()

    # Form queryset.
    qs = Athlete.objects.defer(
        "additional_info",
        "twitter_info",
        "youtube_info",
        "wiki_views_info",
        "site_views_info",
    )

    list_id = None
    try:
        list_id = int(request.GET.get("list_id"))
        athletes_ids = AthletesList.objects.filter(
            user=request.user, pk=list_id
        ).values_list("athletes__id", flat=True)
        qs = qs.filter(pk__in=athletes_ids)
    except (ValueError, TypeError):
        pass

    if filters:
        for field, val in filters.items():
            # Process filtering by properties.
            if field == "market_export":
                if val == "true":
                    qs = qs.exclude(domestic_market=F("location_market"))
                else:
                    qs = qs.filter(domestic_market=F("location_market"))
                continue

            if field == "age":
                val = val.split("-")

                if len(val) == 2 and val[0].isdigit() and val[1].isdigit():
                    for i, _ in enumerate(val):
                        today = datetime.date.today()
                        val[i] = datetime.date(
                            today.year - int(val[i]), today.month, today.day
                        )

                    qs = qs.filter(birthday__gte=val[1], birthday__lte=val[0])
                continue

            model_field = Athlete._meta.get_field(field)

            if field in ("marketability", "instagram", "twitter"):
                val = val.split("-")
                if len(val) == 2 and val[0].isdigit() and val[1].isdigit():
                    qs = qs.filter(**{f"{field}__gte": val[0], f"{field}__lte": val[1]})
            elif field in ("domestic_market", "location_market"):
                country_val = [
                    code
                    for code, name in COUNTRIES.items()
                    if val.lower() in name.lower()
                ]
                qs = qs.filter(**{f"{field}__in": country_val})
            elif model_field.choices:
                qs = qs.filter(**{f"{field}__in": val.split(",")})
            elif model_field.get_internal_type() == "BooleanField":
                qs = qs.filter(**{f"{field}": val == "true"})
            else:
                qs = qs.filter(**{f"{field}__unaccent__icontains": val})

    if search:
        # Smart search by name, domestic_market, gender,
        # location_market, team, category fields.
        country_val = [
            code for code, name in COUNTRIES.items() if search.lower() in name.lower()
        ]

        qs = qs.filter(
            Q(name__unaccent__icontains=search)
            | Q(domestic_market__in=country_val)
            | Q(gender__icontains=search)
            | Q(location_market__in=country_val)
            | Q(team__unaccent__icontains=search)
            | Q(category__icontains=search)
        )

    # Count filtered rows.
    if filters or search or list_id:
        filtered = qs.count()
    else:
        filtered = total  # no need to count filtered rows

    qs = qs.order_by(*order)

    # Pagination.
    qs = qs[start : start + length]

    return {
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": filtered,
        "data": _serialize_qs(qs),
    }


@login_required
def athletes_api(request):
    return JsonResponse(_athletes_api(request))


def _teams_api(request):
    """Return filtered/sorted/paginated list of teams for datatables."""
    draw, start, length, order, search, filters = _process_datatables_params(
        request.GET
    )

    # Count all rows.
    total = Team.objects.count()

    # Form queryset.
    qs = Team.objects.defer(
        "additional_info", "youtube_info", "wiki_views_info", "site_views_info"
    )

    list_id = None
    try:
        list_id = int(request.GET.get("list_id"))
        teams_ids = TeamsList.objects.filter(user=request.user, pk=list_id).values_list(
            "teams__id", flat=True
        )
        qs = qs.filter(pk__in=teams_ids)
    except (ValueError, TypeError):
        pass

    if filters:
        for field, val in filters.items():
            if field == "twitter":
                field = "twitter_info"

            model_field = Team._meta.get_field(field)

            if field == "twitter_info":
                # TODO[Mike] Fix this.
                val = val.split("-")
                if len(val) == 2 and val[0].isdigit() and val[1].isdigit():
                    qs = qs.filter(
                        twitter_info__followers_count__gte=val[0],
                        twitter_info__followers_count__lte=val[1],
                    )
            elif field == "location_market":
                country_val = [
                    code
                    for code, name in COUNTRIES.items()
                    if val.lower() in name.lower()
                ]
                qs = qs.filter(**{f"{field}__in": country_val})
            elif field == "league":
                qs = qs.filter(**{f"{field}__name__unaccent__icontains": val})
            elif model_field.choices:
                qs = qs.filter(**{f"{field}__in": val.split(",")})
            elif model_field.get_internal_type() == "BooleanField":
                qs = qs.filter(**{f"{field}": val == "true"})
            else:
                qs = qs.filter(**{f"{field}__unaccent__icontains": val})

    if search:
        # Smart search by name, gender,
        # location_market, league, category fields.
        country_val = [
            code for code, name in COUNTRIES.items() if search.lower() in name.lower()
        ]

        qs = qs.filter(
            Q(name__unaccent__icontains=search)
            | Q(gender__icontains=search)
            | Q(location_market__in=country_val)
            | Q(league__name__unaccent__icontains=search)
            | Q(category__icontains=search)
        )

    # Count filtered rows.
    if filters or search or list_id:
        filtered = qs.count()
    else:
        filtered = total  # no need to count filtered rows

    qs.select_related("league")

    qs = qs.order_by(*order)

    # Pagination.
    qs = qs[start : start + length]

    return {
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": filtered,
        "data": _serialize_qs(qs),
    }


@login_required
def teams_api(request):
    return JsonResponse(_teams_api(teams_api))


@login_required
def athletes_list_api(request):
    """Create or Update Athletes_list."""
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if request.method == "POST":
            # Create Athletes_list.
            form = AthletesListForm(request.POST)
            if form.is_valid():
                athletes_ids = request.POST.get("id_athletes", "").split(",")
                athletes_ids = [pk for pk in athletes_ids if pk.isdigit()]

                athletes_list = form.save(commit=False)
                athletes_list.user = request.user

                athletes_list.save()
                athletes_list.athletes.add(*athletes_ids)

                return JsonResponse(
                    {
                        "id": athletes_list.pk,
                        "name": athletes_list.name,
                        "success": True,
                    }
                )
        elif request.method == "PUT":
            # Add Athletes to Athletes_list.
            body = QueryDict(request.body)
            list_id = body.get("list_id")
            athletes_ids = body.getlist("athletes_ids[]")
            athletes_ids = [int(pk) for pk in athletes_ids if pk.isdigit()]

            if athletes_ids and list_id and list_id.isdigit():
                athletes_list = AthletesList.objects.filter(
                    pk=list_id, user=request.user
                ).first()

                if athletes_list:
                    old = athletes_list.athletes.values_list("id", flat=True)

                    athletes_list.athletes.add(
                        *[pk for pk in athletes_ids if pk not in old]
                    )

                    return JsonResponse(
                        {
                            "id": athletes_list.pk,
                            "name": athletes_list.name,
                            "success": True,
                        }
                    )

        return JsonResponse({"success": False})

    raise Http404


@login_required
def athletes_export_api(request):
    """Export athletes to csv file."""
    ids = request.GET.get("ids", "").split(",")
    ids = [pk for pk in ids if pk.isdigit()]
    ids = ids or [-1]  # not existing id

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="athletes.csv"'

    qs = Athlete.objects.filter(pk__in=ids).defer(
        "additional_info",
        "twitter_info",
        "youtube_info",
        "wiki_views_info",
        "site_views_info",
    )
    content = _serialize_qs(qs)

    fields = [
        "name",
        "domestic_market",
        "age",
        "gender",
        "location_market",
        "team",
        "category",
        "marketability",
        "optimal_campaign",
        "market_export",
        "instagram",
        "twitter",
    ]

    writer = csv.writer(response)
    writer.writerow(fields)
    for athletes in content:
        row = [athletes[key] for key in fields]
        writer.writerow(row)

    return response


@login_required
def add_athlete_to_lists_api(request):
    """Add an athlete to the lists."""
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        athlete_id = request.POST.get("athlete")
        # Only int values are allowed.
        athlete_id = athlete_id if athlete_id.isdigit() else -1

        new_lists_ids = request.POST.getlist("athletes_lists")
        # Only int values are allowed.
        new_lists_ids = {int(v) for v in new_lists_ids if v.isdigit()}

        athlete = get_object_or_404(
            Athlete.objects.prefetch_related("athletes_lists"), pk=athlete_id
        )
        old_lists_ids = {
            athletes_list.pk
            for athletes_list in athlete.athletes_lists.all()
            if athletes_list.user == request.user  # filter by current user
        }

        athletes_lists = AthletesList.objects.filter(
            pk__in=new_lists_ids ^ old_lists_ids,
            user=request.user,  # filter by current user
        )

        for athletes_list in athletes_lists:
            if athletes_list.pk in new_lists_ids - old_lists_ids:
                athletes_list.athletes.add(athlete)  # add
            elif athletes_list.pk in old_lists_ids - new_lists_ids:
                athletes_list.athletes.remove(athlete)  # remove

        return JsonResponse({"success": True})

    raise Http404


@login_required
def add_team_to_lists_api(request):
    """Add an team to the lists."""
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        team_id = request.POST.get("team")
        # Only int values are allowed.
        team_id = team_id if team_id.isdigit() else -1

        new_lists_ids = request.POST.getlist("teams_lists")
        # Only int values are allowed.
        new_lists_ids = {int(v) for v in new_lists_ids if v.isdigit()}

        team = get_object_or_404(
            Team.objects.prefetch_related("teams_lists"), pk=team_id
        )
        old_lists_ids = {
            teams_list.pk
            for teams_list in team.teams_lists.all()
            if teams_list.user == request.user  # filter by current user
        }

        teams_lists = TeamsList.objects.filter(
            pk__in=new_lists_ids ^ old_lists_ids,
            user=request.user,  # filter by current user
        )

        for teams_list in teams_lists:
            if teams_list.pk in new_lists_ids - old_lists_ids:
                teams_list.teams.add(team)  # add
            elif teams_list.pk in old_lists_ids - new_lists_ids:
                teams_list.teams.remove(team)  # remove

        return JsonResponse({"success": True})

    raise Http404


@login_required
def add_league_to_lists_api(request):
    """Add an league to the lists."""
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        league_id = request.POST.get("league")
        # Only int values are allowed.
        league_id = league_id if league_id.isdigit() else -1

        new_lists_ids = request.POST.getlist("leagues_lists")
        # Only int values are allowed.
        new_lists_ids = {int(v) for v in new_lists_ids if v.isdigit()}

        league = get_object_or_404(
            League.objects.prefetch_related("leagues_lists"), pk=league_id
        )
        old_lists_ids = {
            leagues_list.pk
            for leagues_list in league.leagues_lists.all()
            if leagues_list.user == request.user  # filter by current user
        }

        leagues_lists = LeaguesList.objects.filter(
            pk__in=new_lists_ids ^ old_lists_ids,
            user=request.user,  # filter by current user
        )

        for leagues_list in leagues_lists:
            if leagues_list.pk in new_lists_ids - old_lists_ids:
                leagues_list.leagues.add(league)  # add
            elif leagues_list.pk in old_lists_ids - new_lists_ids:
                leagues_list.leagues.remove(league)  # remove

        return JsonResponse({"success": True})

    raise Http404


@login_required
def follow_api(request, class_name, pk):
    """Follow/Unfollow athlete, team, league."""
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        subscribe = request.POST.get("subscribe") == "true"
        profile, _ = Profile.objects.get_or_create(user=request.user)
        followed = getattr(profile, f"followed_{class_name}s", None)

        if not followed:
            raise Http404

        if subscribe:
            followed.add(pk)
        else:
            followed.remove(pk)

        return JsonResponse({"success": True})

    raise Http404


@login_required
def autocomplete_api(request, class_name):
    """Autocomplete for athlete, team, league."""
    limit = 5
    result = set([])

    cls = {"league": League, "team": Team, "athlete": Athlete}.get(class_name)

    if cls:
        search = request.GET.get("q", "")
        fields = request.GET.get("fields", "").split(",")
        fields = [] if fields == [""] else fields

        # Search for similar name in database.
        if (not fields and class_name == "athlete") or (
            "name" in fields and "team" in fields
        ):
            # Search in name and team fields (2 fields).
            result.update(
                cls.objects.annotate(
                    similarity_name=TrigramSimilarity("name", search),
                    similarity_team=TrigramSimilarity("team", search),
                    similarity=Greatest(F("similarity_name"), F("similarity_team")),
                    value=Case(
                        When(
                            Q(similarity_team__gt=F("similarity_name")), then=F("team")
                        ),
                        default=F("name"),
                        output_field=CharField(),
                    ),
                )
                .filter(similarity__gt=0.1)
                .order_by("-similarity")
                .values_list("value", flat=True)[:limit]
            )
        elif "name" in fields or "team" in fields:
            # Search in name or team fields (1 field).
            field = "name" if "name" in fields else "team"

            result.update(
                cls.objects.annotate(similarity=TrigramSimilarity(field, search))
                .filter(similarity__gt=0.1)
                .order_by("-similarity")
                .values_list(field, flat=True)[:limit]
            )

        # Check categories.
        if not fields or "category" in fields:
            i = 0
            for val in CATEGORIES.values():
                if search.lower() in val.lower():
                    result.add(val)
                    i += 1
                    if i >= limit:
                        break

        # Check countries.
        if not fields or "country" in fields:
            i = 0
            for val in COUNTRIES.values():
                if search.lower() in val.lower():
                    result.add(val)
                    i += 1
                    if i >= limit:
                        break

        # Check genders.
        if not fields or "gender" in fields:
            for val in ("male", "female"):
                if search.lower() in val:
                    result.add(val)

    return JsonResponse(list(result), safe=False)
