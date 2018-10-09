from django.urls import path

from core.views.api import (athletes_api, athletes_export_api,
                            athletes_list_api, add_athlete_to_lists_api,
                            add_team_to_lists_api)
from core.views.pages import (crm_page, about_page, login_page, logout_page,
                              ParseTeamView, ParseTeamsView, athlete_page,
                              terms_page, map_page, team_page)

app_name = "Athletes"

urlpatterns = [
    path('', about_page, name='home'),
    path('crm', crm_page, name='crm'),
    path('athletes_list', athletes_list_api, name='athletes_list'),
    path('athlete/<str:slug>', athlete_page, name='athlete'),
    path('api/athletes_list', add_athlete_to_lists_api, name='athletes_list'),
    path('team/<int:pk>', team_page, name='team'),
    path('api/teams_list', add_team_to_lists_api, name='teams_list'),
    path('terms', terms_page, name='terms'),
    path('map', map_page, name='map'),
    path('team', ParseTeamView.as_view(), name='team'),
    path('teams', ParseTeamsView.as_view(), name='teams'),
    path('export/athletes', athletes_export_api, name='athletes_export'),
    path('api/athletes', athletes_api, name='athletes-api'),
    path('login', login_page, name='login'),
    path('logout', logout_page, name='logout'),
]
