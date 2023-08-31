# -*- coding: UTF-8 -*-

from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from django.utils.safestring import mark_safe
import pytz
from its_utils.app_cron.models import CronLog
from .models import Cron, CronResult
from django.conf import settings

from its_utils.app_admin.action_admin import ActionAdmin


# Позволяет определить, какие результаты получать в inline-таблицу
# См. здесь: http://stackoverflow.com/questions/2101979/django-admin-filter-objects-for-inline-formset
class CustomCronFormSet(BaseInlineFormSet):
    # В self.instance будет именно тот крон, для которого нужно вывести данные
    # Получаем срез по 100 последних элементов
    def get_queryset(self):
        if not hasattr(self,
                       '_queryset'):  # Это условие не выполняется, но почему-то срез берется именно указанного размера
            # qs = super(CustomCronFormSet, self).get_queryset().order_by("-start")[:99]
            qs = super(CustomCronFormSet, self).get_queryset().order_by("-id")[:99]
            self._queryset = qs
        return self._queryset


class CronResultInline(admin.TabularInline):
    model = CronResult
    fields = 'start', 'end', 'time', 'text'
    readonly_fields = fields
    extra = 0
    formset = CustomCronFormSet  # Это позволит нам фильтровать результаты


class CronAdmin(ActionAdmin):
    list_display = ('__unicode__', 'run_url', 'name', 'path', 'started_time', 'string', 'repeat_seconds',
                    'active', 'timeout', 'concurrency', 'process_filter', 'parameters', 'description')
    list_editable = 'name', 'path', 'string', 'active', 'repeat_seconds', 'timeout', 'concurrency', 'process_filter'
    inlines = [CronResultInline]
    actions = ('kill_cron', 'grep_cron_process')

    def run_url(self, obj):
        url = '/its/cron/%s/' % obj.pk
        return mark_safe(u'<a href=%s target="_blank">%s</a>' % (url, u'Запустить'))

    run_url.allow_tags = True
    run_url.short_description = u'Запустить крон'


# class CronResultAdmin(ActionAdmin):
#     list_display = '__unicode__', 'start', 'finished', 'end', 'time', 'text', 'cron_started'
#     list_display_links = list_display
#     list_filter = ['cron', 'finished']
#     raw_id_fields = 'cron_log',
#     actions = 'is_alive',


admin.site.register(Cron, CronAdmin)
#admin.site.register(CronResult, CronResultAdmin)
#admin.site.register(CronLog, CronLogAdmin)

from its_utils.app_admin.auto_register import auto_register
auto_register("app_cron")
