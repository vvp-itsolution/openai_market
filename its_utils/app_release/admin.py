# -*- coding: UTF-8 -*-

from django.contrib import admin

from .models import *


class ApplicationAdmin(admin.ModelAdmin):

    pass


class ReleaseAdmin(admin.ModelAdmin):

    list_display = 'datetime', 'application', 'state', 'comment'
    list_display_links = list_display
    ordering = '-id', '-datetime'


admin.site.register(Application, ApplicationAdmin)
admin.site.register(Release, ReleaseAdmin)
