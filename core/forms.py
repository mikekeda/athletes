from django import forms
from django.utils.translation import ugettext_lazy as _

from core.constans import CATEGORIES, COUNTRIES


class TeamForm(forms.Form):
    team_wiki_url = forms.URLField(label='Team wiki url')
    location_market = forms.ChoiceField(
        choices=[('','Not set')] + list(COUNTRIES.items())
    )
    gender = forms.ChoiceField(
        choices=[('','Not set')] + [("male", _("Male")),
                                    ("female", _("Female"))]
    )
    category = forms.ChoiceField(
        choices=[('','Not set')] + list(CATEGORIES.items())
    )
