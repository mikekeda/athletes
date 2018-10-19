from bs4 import BeautifulSoup
from django import forms
from django.core.exceptions import ValidationError

from core.models import League, Team, AthletesList


def validate_selector(selector: str):
    soup = BeautifulSoup('', 'html.parser')
    try:
        soup.select(selector)
        return
    except ValueError:
        pass

    raise ValidationError('Not valid selector')


class TeamForm(forms.ModelForm):
    """ Team form. """

    def validate_unique(self):
        """ Skip validate_unique to use custom get or create logic. """
        pass

    class Meta:
        model = Team
        exclude = ('name', 'longitude', 'latitude', 'photo', 'league',
                   'additional_info', 'twitter_info', 'youtube_info')


class LeagueForm(forms.ModelForm):
    """ League form. """
    selector = forms.CharField(
        initial="table tr > td:nth-of-type(1) > a",
        validators=[validate_selector],
    )

    def validate_unique(self):
        """ Skip validate_unique to use custom get or create logic. """
        pass

    class Meta:
        model = League
        exclude = ('name', 'photo', 'additional_info', 'twitter_info',
                   'youtube_info')


class AthletesListForm(forms.ModelForm):
    """ AthletesList form. """

    class Meta:
        model = AthletesList
        exclude = ('user', 'athletes')
