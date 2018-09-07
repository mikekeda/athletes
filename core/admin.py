from django.contrib import admin
from easy_select2 import select2_modelform
from import_export.admin import ImportExportModelAdmin

from core.models import Athlete, Team

AthleteForm = select2_modelform(Athlete)
TeamForm = select2_modelform(Team)


def update_data_from_wiki(_, __, queryset):
    """ Update information for selected athletes with data from Wikipedia. """
    for obj in queryset:
        obj.get_data_from_wiki()
        obj.save()


update_data_from_wiki.short_description = "Update data from Wikipedia"


class AthleteAdmin(ImportExportModelAdmin):
    list_filter = ('gender', 'category',)
    list_display = ('name',)
    search_fields = ('name',)
    form = AthleteForm
    actions = [update_data_from_wiki]


class TeamAdmin(ImportExportModelAdmin):
    list_filter = ('gender', 'category',)
    list_display = ('team',)
    search_fields = ('team',)
    form = TeamForm
    actions = [update_data_from_wiki]


admin.site.register(Athlete, AthleteAdmin)
admin.site.register(Team, TeamAdmin)
