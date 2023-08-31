# coding: utf-8
from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from its_utils.app_logger.models.abs_log_record import AbsLogRecord
from django.contrib import admin

class LogRecord(AbsLogRecord):
    """
    Описывает сообщение в логе
    """

    from its_utils.django_postgres_fuzzycount.fuzzycount import FuzzyCountManager
    objects = FuzzyCountManager()

    class Meta:
        app_label = 'app_logger'
        indexes = [
            models.Index(fields=['date', 'type']),
        ]

    class Admin(admin.ModelAdmin):
        list_filter = ['app', 'level', 'type']
        list_display = ('short_pathname', 'type', 'level', 'dt_with_seconds', 'tag_link', 'some_msg')
        readonly_fields = ['id', 'rendered_body_html']
        search_fields = 'message', 'tag'
        # Следующий запрос не использует индекс на поле date_time,
        # поэтому при множестве логов выполняется очень долго (десятки минут)
        #     SELECT DISTINCT DATE_TRUNC('month', "app_logger_logrecord"."date_time") AS "datefield"
        #     FROM "app_logger_logrecord"
        #     WHERE "app_logger_logrecord"."date_time" IS NOT NULL
        #     ORDER BY "datefield" ASC
        # Если группировка по дате очень нужна, то надо добавить индекс:
        #     DATE_TRUNC('month', "app_logger_logrecord"."date_time")
        # date_hierarchy = 'date_time'
        show_full_result_count = False
        raw_id_fields = 'type', 'script', 'app'
        list_select_related = 'script', 'type',  # см. list_display: type, short_pathname

        def rendered_body_html(self, obj):
            return format_html(u"{}", mark_safe(obj.exception_info))

        # def get_queryset(self, request):
        #     qs = super(LogRecordAdmin, self).get_queryset(request)
        #     now = timezone.now()
        #
        #     if not request.GET:
        #         qs = qs.filter(date_time__day=now.day, date_time__month=now.month, date_time__year=now.year)
        #         # setattr(qs, "count", lambda: 1000)
        #
        #     self.message_user(request, mark_safe(
        #         "используйте такую строку чтобы отфильтровать по времени?"
        #         "<a href='?date_time__gt=2017-07-14 16:30&date_time__lt=2017-07-14 16:31'>"
        #         "?date_time__gt=2017-07-14 16:30&date_time__lt=2017-07-14 16:31"
        #         "</a>"
        #     ))
        #
        #     return qs

        def dt_with_seconds(self, obj):
            return timezone.localtime(obj.date_time).strftime('%d.%m.%Y %H:%M:%S')

        dt_with_seconds.short_description = u'Время'
        dt_with_seconds.admin_order_field = 'date_time'

        def short_pathname(self, obj):
            return "...{}".format(obj.script.pathname[-30:])

        def some_msg(self, obj):
            return obj.message[:200]

        def tag_link(self, obj):
            if obj.tag:
                return format_html(
                    '<a href="../logrecord/?tag={tag}">{tag}</a>',
                    tag=obj.tag,
                )
            return '-'

        some_msg.short_description = u'Сообщение'

    def before_save(self):
        pass
