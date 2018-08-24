from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from core.models import Athlete


admin.site.register(Athlete, ImportExportModelAdmin)
