import logging

from django.core.exceptions import FieldError

from rest_framework import viewsets, status
from rest_framework.response import Response

from core.models import Athlete, Team
from core.views.api import _athletes_api, _teams_api

log = logging.getLogger('athletes')


class AthleteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Athlete.objects.all()

    def list(self, request, *args, **kwargs):
        try:
            return Response(_athletes_api(request._request))
        except (FieldError, TypeError) as e:
            log.warning("AthleteViewSet: Failed processing api request %s", repr(e))
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Team.objects.all()

    def list(self, request, *args, **kwargs):
        try:
            return Response(_teams_api(request._request))
        except (FieldError, TypeError) as e:
            log.warning("TeamViewSet: Failed processing api request %s", repr(e))
            return Response({{'error': str(e)}}, status=status.HTTP_400_BAD_REQUEST)
