from bs4 import BeautifulSoup

from django import forms
from django.core.exceptions import ValidationError

from core.constans import COUNTRIES, CATEGORIES
from core.models import Team


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
        exclude = ('team', 'longitude', 'latitude', 'additional_info')


class TeamsForm(forms.Form):
    wiki = forms.URLField()
    location_market = forms.ChoiceField(
        choices=[('', '---------')] + list(COUNTRIES.items())
    )
    gender = forms.ChoiceField(
        choices=[('', '---------')] + [("male", "Male"),
                                       ("female", "Female")]
    )
    category = forms.ChoiceField(
        choices=[('', '---------')] + list(CATEGORIES.items())
    )
    selector = forms.CharField(
        initial="table tr > td:nth-of-type(1) > a",
        validators=[validate_selector],
    )
