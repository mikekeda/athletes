from django.contrib import admin
from django.db.models import Q
from django.db.utils import DataError
from easy_select2 import select2_modelform
from import_export.admin import ImportExportModelAdmin

from core.models import Athlete, Team

AthleteForm = select2_modelform(Athlete)
TeamForm = select2_modelform(Team)


class DomesticMarketListFilter(admin.SimpleListFilter):
    """ Filter by emptiness. """
    title = 'domestic market'
    parameter_name = 'has_domestic_market'

    def lookups(self, request, model_admin):
        return (
            ('not_empty', 'Not empty'),
            ('empty',  'Empty'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'not_empty':
            return queryset.filter(domestic_market__isnull=False).exclude(
                domestic_market='')
        elif self.value() == 'empty':
            return queryset.filter(Q(domestic_market__isnull=True) | Q(
                domestic_market__exact=''))


def update_data_from_wiki(_, __, queryset):
    """ Update information for selected athletes with data from Wikipedia. """
    for obj in queryset:
        obj.get_data_from_wiki()
        obj.save()


def update_location(_, __, queryset):
    """ Update location for selected teams. """
    for obj in queryset:
        obj.get_location()
        obj.save()


def update_twitter(_, __, queryset):
    """ Update twitter followers for selected athletes. """
    for obj in queryset:
        obj.get_twitter_info()
        try:
            obj.save()
        except DataError:
            # Remove twitter_info and try to save one more time.
            obj.twitter_info = []
            super(Athlete, obj).save()


update_data_from_wiki.short_description = "Update data from Wikipedia"


class AthleteInline(admin.TabularInline):
    model = Athlete
    form = AthleteForm
    extra = 1


class AthleteAdmin(ImportExportModelAdmin):
    readonly_fields = ('added', 'updated')
    list_filter = ('gender', 'category', DomesticMarketListFilter)
    list_display = ('name',)
    search_fields = ('name',)
    form = AthleteForm
    actions = [update_data_from_wiki, update_location, update_twitter]


class TeamAdmin(ImportExportModelAdmin):
    readonly_fields = ('added', 'updated')
    list_filter = ('gender', 'category')
    list_display = ('team',)
    search_fields = ('team',)
    form = TeamForm
    actions = [update_data_from_wiki, update_location]
    inlines = [AthleteInline]


admin.site.register(Athlete, AthleteAdmin)
admin.site.register(Team, TeamAdmin)
