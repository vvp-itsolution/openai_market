# -*- coding: utf-8 -*-
from django.db import migrations


def rm_orphans(apps, schema_editor):
    """Удаляет дубликаты LoggedScripts перед добавлением
    `unique=True` к pathname. Оставляет первый созданный LoggedScript.
    """
    LogRecord = apps.get_model('app_logger', 'LogRecord')

    db_alias = schema_editor.connection.alias
    records = LogRecord.objects.using(db_alias)

    print()
    print('deleting orphans: ', end='')
    print(records.filter(app__isnull=True).delete())


class Migration(migrations.Migration):
    """Отдельно от последующей миграции для предотвращения ошибки:

    django.db.utils.OperationalError: ОШИБКА:  нельзя выполнить ALTER TABLE "app_logger_logrecord",
    так как с этим объектом связаны отложенные события триггеров.

    https://stackoverflow.com/a/12838113
    """

    dependencies = [
        ('app_logger', '0008_logtype_postpone'),
    ]

    operations = [
        migrations.RunPython(rm_orphans, migrations.RunPython.noop),
    ]
