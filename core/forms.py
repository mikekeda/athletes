from django import forms
from core.models import Team


class TeamForm(forms.ModelForm):
    """ Team form. """

    def validate_unique(self):
        """ Skip validate_unique to use custom get or create logic. """
        pass

    class Meta:
        model = Team
        exclude = ('team', 'longitude', 'latitude', 'additional_info')
