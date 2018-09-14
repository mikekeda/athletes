from django import forms

from core.constans import COUNTRIES, CATEGORIES
from core.models import Team


class TeamForm(forms.ModelForm):
    """ Team form. """

    def validate_unique(self):
        """ Skip validate_unique to use custom get or create logic. """
        pass

    class Meta:
        model = Team
        exclude = ('team', 'longitude', 'latitude', 'additional_info')


class TeamsForm(forms.Form):
    wiki = forms.CharField(widget=forms.Textarea)
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
