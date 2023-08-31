# Функция создана для транзакционного апдейта jsonfield
import json
import six

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Func

if not six.PY2:
    from typing import Type


def _get_model(instance):
    # type: (models.Model) -> Type[models.Model]
    try:
        return instance._meta.model
    except AttributeError:
        if not isinstance(instance, models.Model):
            raise TypeError
        return type(instance)


class JsonbSet(Func):
    # https://stackoverflow.com/a/45308014
    function = 'jsonb_set'
    template = "%(function)s(%(expressions)s, '{%(key)s}','%(value)s', %(create_missing)s)"
    arity = 1

    def __init__(
        self,
        expression,  # type: str
        key,  # type: str
        value,  # type: str
        create_missing=True,  # type: bool
        **extra
    ):
        super().__init__(
            expression,
            key=json.dumps(key, cls=DjangoJSONEncoder),
            value=json.dumps(value, cls=DjangoJSONEncoder),
            create_missing='true' if create_missing else 'false',
            **extra,
        )


def jsonfield_update(
            instance,  # type: models.Model
            jsonfield_name,  # type: str
            key,  # type: str
            value,  # type: str
            create_missing=True,  # type: bool
            refresh_from_db=True,  # type: bool
    ):  # type: (...) -> None
    """Обновляет поля в JSONField с блокировкой записи.

    Usage:
        my_article = MyArticle.objects.first()
        my_article.meta_tags == {'keywords': 'ключевые слова', 'foo': 42}
        jsonfield_update(my_article, 'meta_tags', 'description', 'описание')
        jsonfield_update(my_article, 'meta_tags', 'foo', 'bar')
        my_article.meta_tags == {
            'keywords': 'ключевые слова',
            'description': 'описание',
            'foo': 'bar',
        }

    :param instance: объект из БД для обновления
    :param jsonfield_name: название jsonfield-поля
    :param key: ключ
    :param value: значение
    :param create_missing: создать ключ при отсутствии
    :param refresh_from_db: получить записанное значение из БД

    На первом этапе только первый уровень вложенности

    см. также:
        https://docs.djangoproject.com/en/3.0/ref/models/querysets/#select-for-update
    """
    # Получаем модель
    model_cls = _get_model(instance)

    # Обновляем
    model_cls.objects \
        .filter(pk=instance.pk) \
        .update(**{
            jsonfield_name: JsonbSet(
                jsonfield_name,
                key=key, value=value,
                create_missing=create_missing,
            )
        })

    # Актуализация старого инстанса модели
    if refresh_from_db:
        instance.refresh_from_db(fields=[jsonfield_name])
