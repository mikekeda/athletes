from django.urls import path

from core.views.api import (athletes_api, athletes_export_api,
                            athletes_list_api, add_athlete_to_lists_api,
                            add_team_to_lists_api, add_league_to_lists_api,
                            follow_api, autocomplete_api)
from core.views.pages import (crm_page, about_page, login_page, logout_page,
                              ParseTeamView, ParseLeagueView, athlete_page,
                              terms_page, map_page, team_page, league_page,
                              country_page, ProfileView,
                              compare_athletes_page)

app_name = "Athletes"

urlpatterns = [
    path('', about_page, name='home'),
    path('crm', crm_page, name='crm'),
    path('athletes_list', athletes_list_api, name='athletes_list'),
    path('athlete/<str:slug>', athlete_page, name='athlete'),
    path('compare/athletes', compare_athletes_page, name='compare_athletes'),
    path('api/athletes_list', add_athlete_to_lists_api, name='athletes_list'),
    path('team/<int:pk>', team_page, name='team'),
    path('league/<int:pk>', league_page, name='league'),
    path('country/<str:code>', country_page, name='country'),
    path('api/teams_list', add_team_to_lists_api, name='teams_list'),
    path('api/leagues_list', add_league_to_lists_api, name='leagues_list'),
    path('api/<str:class_name>/<int:pk>/follow', follow_api, name='follow_api'),
    path('api/<str:class_name>/autocomplete', autocomplete_api,
         name='autocomplete_api'),
    path('user/<str:username>', ProfileView.as_view(), name='user'),
    path('terms', terms_page, name='terms'),
    path('map', map_page, name='map'),
    path('team', ParseTeamView.as_view(), name='team_parse'),
    path('league', ParseLeagueView.as_view(), name='league_parse'),
    path('export/athletes', athletes_export_api, name='athletes_export'),
    path('api/athletes', athletes_api, name='athletes-api'),
    path('login', login_page, name='login'),
    path('logout', logout_page, name='logout'),
]
