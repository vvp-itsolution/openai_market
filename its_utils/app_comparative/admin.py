# coding: utf-8

from django.contrib import admin

from its_utils.app_comparative.models import Compared
from its_utils.app_comparative.models.snippets import Snippet


@admin.register(Compared)
class ComparedAdmin(admin.ModelAdmin):
    list_display = ('id', 'show_url1', 'show_url2', 'run_url', 'last_compare')

    def run_url(self, obj):
        url = '/its/compare/%s/' % obj.pk
        return u'<a href=%s target="_blank">%s</a>' % (url, u'Сравнить')

    run_url.allow_tags = True
    run_url.short_description = u'Сравнить html'

    def show_url1(self, obj):
        return u'<a href="{0}" target="_blank">{0}</a>'.format(obj.url1)

    show_url1.allow_tags = True
    show_url1.short_description = u'URL 1'

    def show_url2(self, obj):
        return u'<a href="{0}" target="_blank">{0}</a>'.format(obj.url2)

    show_url2.allow_tags = True
    show_url2.short_description = u'URL 2'


@admin.register(Snippet)
class SnippetAdmin(admin.ModelAdmin):
    list_display = ('id', 'level', 'snippet')
