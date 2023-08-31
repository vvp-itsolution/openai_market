# -*- coding: UTF-8 -*-
from django.contrib import admin
from django.db import models

from . import CronResult
from .cron import Cron
from ...app_admin.action_admin import ActionAdmin


class CronLog(models.Model):
    """Логгирует выполнение крона в принципе, а не отдельных функций
    """

    started = models.DateTimeField(null=True)
    stopped = models.DateTimeField(null=True)
    process = models.IntegerField(default=0)
    finished = models.BooleanField(default=False)

    @property
    def run_time(self):
        if self.started and self.stopped:
            return self.stopped - self.started

    def __str__(self):
        return "cron at {}".format(self.started)

    class Admin(ActionAdmin):
        class CronResultAdminInline(admin.TabularInline):
            model = CronResult
            extra = 0
            fields = 'cron', 'start', 'end', 'text'
            readonly_fields = fields

            # ordering = '-is_admin', '-id'

            def has_delete_permission(self, request, obj=None):
                return False

            def has_add_permission(self, request, obj=None):
                return False


        list_display = 'started', 'finished', 'stopped', 'process', 'run_time'
        list_display_links = list_display
        list_filter = ['finished', 'process']
        inlines = [CronResultAdminInline]