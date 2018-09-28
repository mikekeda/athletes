from django.urls import path

from .views import (crm_page, about_page, login_page, logout_page,
                    athletes_api, ParseTeamView, ParseTeamsView, terms,
                    map_page, athlete_page, team_page, athletes_export_page,
                    athletes_list_api)


app_name = "Athletes"

urlpatterns = [
    path('', about_page, name='home'),
    path('crm', crm_page, name='crm'),
    path('athletes_list', athletes_list_api, name='athletes_list'),
    path('athlete/<str:slug>', athlete_page, name='athlete'),
    path('team/<int:pk>', team_page, name='team'),
    path('terms', terms, name='terms'),
    path('map', map_page, name='map'),
    path('team', ParseTeamView.as_view(), name='team'),
    path('teams', ParseTeamsView.as_view(), name='teams'),
    path('export/athletes', athletes_export_page, name='athletes_export'),
    path('api/athletes', athletes_api, name='athletes-api'),
    path('login', login_page, name='login'),
    path('logout', logout_page, name='logout'),
]
