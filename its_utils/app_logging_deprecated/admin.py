
# -*- coding: utf-8 -*-

from django.contrib import admin
from django.utils import timezone
from django.utils.safestring import mark_safe

from its_utils.app_logging.cron_functions import handle_redis_logs
from its_utils.app_logging.models import LogFromRedis, LoggedScript, LogType


class LogFromRedisAdmin(admin.ModelAdmin):
    list_filter = ['level', 'type']
    list_display = ('short_pathname', 'type', 'level', 'dt', 'some_msg', 'dt_with_seconds', )
    readonly_fields = ('id',)
    search_fields = ('pathname', 'msg')
    date_hierarchy = 'date'
    show_full_result_count = False
    raw_id_fields = ['type']

    def get_queryset(self, request):
        # Нано фича, перед показом админики собираем логи)
        handle_redis_logs()
        qs = super(LogFromRedisAdmin, self).get_queryset(request)
        if not request.GET:
            qs=qs.filter(date=timezone.now())
            #setattr(qs, "count", lambda: 1000)
        self.message_user(request, mark_safe("используйте такую строку чтобы отфильтровать по времени?<a href='?dt__gt=2017-07-14 16:30&dt__lt=2017-07-14 16:31'>?dt__gt=2017-07-14 16:30&dt__lt=2017-07-14 16:31</a>"))
        return qs


    def dt_with_seconds(self, obj):
        return obj.dt.strftime('%d.%m.%Y %H:%M:%S')

    def short_pathname(self, obj):
        return "...{}".format(obj.pathname[-30:])



    dt_with_seconds.short_description = u'Дата'

admin.site.register(LogFromRedis, LogFromRedisAdmin)


class LoggedScriptAdmin(admin.ModelAdmin):
    list_display = ('pathname', 'level_save_to_db', 'level_send_email')
    readonly_fields = ('id',)

admin.site.register(LoggedScript, LoggedScriptAdmin)


class LogTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'level_save_to_db', 'level_send_email', 'storage_days', 'count_info')
    readonly_fields = ('id',)

admin.site.register(LogType, LogTypeAdmin)
