from django.contrib import admin
from django.db.models import Q
from easy_select2 import select2_modelform
from import_export.admin import ImportExportActionModelAdmin

from core.models import (Athlete, League, Team, AthletesList, TeamsList,
                         LeaguesList, Profile, TeamArticle)

AthleteForm = select2_modelform(Athlete)
LeagueForm = select2_modelform(League)
TeamForm = select2_modelform(Team)
ProfileForm = select2_modelform(Profile)
TeamArticleForm = select2_modelform(TeamArticle)


class DomesticMarketListFilter(admin.SimpleListFilter):
    """ Filter by emptiness. """
    _field = 'domestic_market'
    title = _field.replace('_', ' ')
    parameter_name = f'has_{_field}'

    def lookups(self, request, model_admin):
        return (
            ('not_empty', 'Not empty'),
            ('empty', 'Empty'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'not_empty':
            return queryset.filter(**{f'{self._field}__isnull': False})\
                .exclude(**{f'{self._field}': ''})
        if self.value() == 'empty':
            return queryset.filter(Q(**{f'{self._field}__isnull': True}) |
                                   Q(**{f'{self._field}__exact': ''}))

        return None


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
        super(type(obj), obj).save()


def update_twitter_info(_, __, queryset):
    """ Update twitter followers for selected athletes. """
    for obj in queryset:
        obj.get_twitter_info()


def update_youtube_info(_, __, queryset):
    """ Update youtube info. """
    for obj in queryset:
        obj.get_youtube_info()
        super(type(obj), obj).save()


def gew_news(_, __, queryset):
    """ Get news for specified teams. """
    for obj in queryset:
        TeamArticle.get_articles(obj)


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
               update_youtube_info, gew_news]
    inlines = [AthleteInline]


class AthletesListAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    readonly_fields = ('added', 'updated')
    list_filter = ('user__username',)
    list_display = ('name',)
    search_fields = ('name',)
    autocomplete_fields = ('athletes',)
    model = AthletesList


class TeamsListAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    readonly_fields = ('added', 'updated')
    list_filter = ('user__username',)
    list_display = ('name',)
    search_fields = ('name',)
    autocomplete_fields = ('teams',)
    model = TeamsList


class LeaguesListAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    readonly_fields = ('added', 'updated')
    list_filter = ('user__username',)
    list_display = ('name',)
    search_fields = ('name',)
    autocomplete_fields = ('leagues',)
    model = LeaguesList


class ProfileAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    model = Profile
    form = ProfileForm
    autocomplete_fields = ('followed_athletes', 'followed_teams',
                           'followed_leagues')


class TeamArticleAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    model = TeamArticle
    form = TeamArticleForm
    search_fields = ('title', 'team__name')
    list_filter = ('publishedAt', 'team__category')


admin.site.register(Athlete, AthleteAdmin)
admin.site.register(League, LeagueAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(AthletesList, AthletesListAdmin)
admin.site.register(TeamsList, TeamsListAdmin)
admin.site.register(LeaguesList, LeaguesListAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(TeamArticle, TeamArticleAdmin)
