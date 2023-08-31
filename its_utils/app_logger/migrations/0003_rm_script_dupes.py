# -*- coding: utf-8 -*-
# Generated by Django 2.1.5 on 2019-03-05 16:15

from django.db import migrations, models


def rm_dupes(apps, schema_editor):
    """Удаляет дубликаты LoggedScripts перед добавлением
    `unique=True` к pathname. Оставляет первый созданный LoggedScript.
    """
    LoggedScript = apps.get_model('app_logger', 'LoggedScript')
    LogRecord = apps.get_model('app_logger', 'LogRecord')

    db_alias = schema_editor.connection.alias
    scripts = LoggedScript.objects.using(db_alias)
    records = LogRecord.objects.using(db_alias)

    duplicate_pathnames = list(
        scripts
        .values('pathname')
        .annotate(c=models.Count('pathname'))
        .filter(c__gte=2)
        .values_list('pathname', flat=True)
    )

    for pathname in duplicate_pathnames:
        same_path_scripts = list(scripts.filter(pathname=pathname).order_by('id'))
        assert len(same_path_scripts) >= 2
        keep_script = same_path_scripts[0]
        rm_scripts = same_path_scripts[1:]
        for script in rm_scripts:
            records.filter(script=script).update(script=keep_script)
            script.delete()


class Migration(migrations.Migration):
    """Отдельно от последующей миграции для предотвращения ошибки:

    django.db.utils.OperationalError: ОШИБКА:  нельзя выполнить ALTER TABLE "app_logger_loggedscript",
    так как с этим объектом связаны отложенные события триггеров.

    https://stackoverflow.com/a/12838113
    """

    dependencies = [
        ('app_logger', '0002_auto_20181108_1655'),
    ]

    operations = [
        migrations.RunPython(rm_dupes),
    ]