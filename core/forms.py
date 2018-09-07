from django import forms
from django.utils.translation import ugettext_lazy as _

from core.constans import CATEGORIES, COUNTRIES
from core.models import Team


class TeamForm(forms.ModelForm):
    """ Team form. """

    class Meta:
        model = Team
        exclude = ('team', 'additional_info',)
