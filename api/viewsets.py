from rest_framework import viewsets
from rest_framework.response import Response

from core.models import Athlete, Team
from core.views.api import _athletes_api, _teams_api


class AthleteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Athlete.objects.all()

    def list(self, request, *args, **kwargs):
        return Response(_athletes_api(request._request))


class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Team.objects.all()

    def list(self, request, *args, **kwargs):
        return Response(_teams_api(request._request))
