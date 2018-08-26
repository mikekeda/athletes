from django.contrib import admin
from easy_select2 import select2_modelform
from import_export.admin import ImportExportModelAdmin

from core.models import Athlete

AthleteForm = select2_modelform(Athlete)


class AthleteAdmin(ImportExportModelAdmin):
    list_filter = ('category',)
    search_fields = ['name']
    form = AthleteForm


admin.site.register(Athlete, AthleteAdmin)
