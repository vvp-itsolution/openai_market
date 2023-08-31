# -*- coding: utf-8 -*-
from django.db import migrations, models


def rm_dupes(apps, schema_editor):
    """Удаляет дубликаты BitrixUserToken перед добавлением
    unique_together={('application', 'user')}.
    Оставляет последний созданный токен (предпочитая активный).
    """
    BitrixUserToken = apps.get_model('bitrix_auth', 'BitrixUserToken')

    db_alias = schema_editor.connection.alias
    tokens = BitrixUserToken.objects.using(db_alias)

    duped_values = list(
        tokens
        .values('application_id', 'user_id')
        .annotate(c=models.Count(('application_id', 'user_id')))
        .filter(c__gte=2)
        .values('application_id', 'user_id')
    )

    rm_ids = set()
    for duped_filter_cond in duped_values:
        dupes = list(
            tokens
            .filter(**duped_filter_cond)
            .order_by('-is_active', '-id')
        )
        # prevent accidental deletion of too many tokens
        assert 1 < len(dupes) <= 3
        keep_token = dupes[0]
        rm_tokens = dupes[1:]
        for token in rm_tokens:
            rm_ids.add(token.id)

    # prevent accidental deletion of too many tokens
    assert len(rm_ids) < 20
    tokens.filter(id__in=rm_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0047_auto_20190117_1129'),
    ]

    operations = [
        migrations.RunPython(rm_dupes, lambda *a, **kw: None),
    ]
