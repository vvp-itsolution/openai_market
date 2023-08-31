# -*- coding: UTF-8 -*-

from django.db import models
from django.db.models import F
from django.db.models.functions import Concat
from django.db.models import Value

from .cron import Cron
from ...app_admin.action_admin import ActionAdmin


class CronResult(models.Model):

    cron = models.ForeignKey(Cron, on_delete=models.PROTECT)
    cron_log = models.ForeignKey('CronLog', null=True, blank=True, on_delete=models.CASCADE)

    start = models.DateTimeField(null=True)
    end = models.DateTimeField(null=True)
    text = models.TextField(null=True)
    finished = models.BooleanField(default=False, db_index=True)

    cron_started = models.DateTimeField(null=True)

    from its_utils.django_postgres_fuzzycount.fuzzycount import FuzzyCountManager
    objects = FuzzyCountManager()

    class Admin(ActionAdmin):
        list_display = '__unicode__', 'start', 'finished', 'end', 'time', 'text', 'cron_started', 'cron_log'
        list_display_links = list_display
        list_filter = ['cron', 'finished']
        raw_id_fields = 'cron_log',
        actions = 'is_alive',

    def append_text(self, text):
        CronResult.objects.filter(pk=self.pk).update(text=Concat(F('text'), Value("\n{}".format(text))))

    class Meta:
        app_label = 'app_cron'

    def time(self):
        if self.start and self.end:
            return self.end - self.start

    def __unicode__(self):
        return u'Result for %s' % self.cron.name

    def is_alive(self):
        return bool(self.cron.grep_cron_process(self.start))
