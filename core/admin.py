from django.contrib import admin
from django.db.models import Q
from django.db.utils import DataError
from easy_select2 import select2_modelform
from import_export.admin import ImportExportActionModelAdmin

from core.models import Athlete, League, Team, AthletesList, TeamsList

AthleteForm = select2_modelform(Athlete)
LeagueForm = select2_modelform(League)
TeamForm = select2_modelform(Team)


class DomesticMarketListFilter(admin.SimpleListFilter):
    """ Filter by emptiness. """
    _field = 'domestic_market'
    title = _field.replace('_', ' ')
    parameter_name = f'has_{_field}'

    def lookups(self, request, model_admin):
        return (
            ('not_empty', 'Not empty'),
            ('empty',  'Empty'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'not_empty':
            return queryset.filter(**{f'{self._field}__isnull': False})\
                .exclude(**{f'{self._field}': ''})
        elif self.value() == 'empty':
            return queryset.filter(Q(**{f'{self._field}__isnull': True})
                                   | Q(**{f'{self._field}__exact': ''}))


def update_data_from_wiki(_, __, queryset):
    """ Update information for selected athletes with data from Wikipedia. """
    for obj in queryset:
        obj.get_data_from_wiki()
        obj.save()


update_data_from_wiki.short_description = "Update data from Wikipedia"


def update_location(_, __, queryset):
    """ Update location for selected teams. """
    for obj in queryset:
        obj.get_location()
        obj.save()


def update_twitter_info(_, __, queryset):
    """ Update twitter followers for selected athletes. """
    for obj in queryset:
        obj.get_twitter_info()
        try:
            obj.save()
        except DataError:
            # Remove twitter_info and try to save one more time.
            obj.twitter_info = {}
            super(Athlete, obj).save()


def update_youtube_info(_, __, queryset):
    """ Update youtube info. """
    for obj in queryset:
        obj.get_youtube_info()
        try:
            obj.save()
        except DataError:
            # Remove youtube_info and try to save one more time.
            obj.youtube_info = {}
            super(Athlete, obj).save()


class AthleteInline(admin.TabularInline):
    model = Athlete
    form = AthleteForm
    extra = 1


class TeamInline(admin.TabularInline):
    model = Team
    form = TeamForm
    extra = 1


class AthleteAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    readonly_fields = ('photo_preview', 'added', 'updated')
    list_filter = ('gender', 'category', DomesticMarketListFilter)
    list_display = ('name',)
    search_fields = ('name',)
    form = AthleteForm
    actions = [update_data_from_wiki, update_location, update_twitter_info,
               update_youtube_info]


class LeagueAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    readonly_fields = ('photo_preview', 'added', 'updated')
    list_filter = ('gender', 'category')
    list_display = ('name',)
    search_fields = ('name',)
    form = LeagueForm
    actions = [update_data_from_wiki, update_twitter_info,
               update_youtube_info]
    inlines = [TeamInline]


class TeamAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    readonly_fields = ('photo_preview', 'added', 'updated')
    list_filter = ('gender', 'category')
    list_display = ('name',)
    search_fields = ('name',)
    form = TeamForm
    actions = [update_data_from_wiki, update_location, update_twitter_info,
               update_youtube_info]
    inlines = [AthleteInline]


class AthletesListAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    list_filter = ('user__username',)
    list_display = ('name',)
    search_fields = ('name',)
    autocomplete_fields = ('athletes',)
    model = AthletesList


class TeamsListListAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    list_filter = ('user__username',)
    list_display = ('name',)
    search_fields = ('name',)
    autocomplete_fields = ('teams',)
    model = TeamsList


admin.site.register(Athlete, AthleteAdmin)
admin.site.register(League, LeagueAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(AthletesList, AthletesListAdmin)
admin.site.register(TeamsList, TeamsListListAdmin)
