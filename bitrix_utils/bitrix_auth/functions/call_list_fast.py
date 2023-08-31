from operator import itemgetter

import six

from settings import ilogger
from ..models import BitrixUserToken
from integration_utils.bitrix24.functions.api_call import DEFAULT_TIMEOUT
from integration_utils.bitrix24.functions.batch_api_call import BatchApiCallError


if not six.PY2:
    from typing import Optional, Iterable, Any, Hashable, Dict, Callable


def _deep_merge(*dicts):  # type: (*dict) -> dict
    """Слияние словарей слева на право:
    >>> d1 = {'foo': None, 'bar': {'baz': 42}}
    >>> d2 = {'foo': {'hello': 'world'}, 'bar': {'quux': 666}}
    >>> _deep_merge(d1, d2)
    {'foo': {'hello': 'world'}, 'bar': {'baz': 42, 'quux': 666}}
    """
    res = {}
    for d in dicts:
        for k, v in d.items():
            if isinstance(v, dict):
                if k in res and not isinstance(res[k], (dict, type(None))):
                    raise ValueError('cannot merge {!r} into {!r}'
                                     .format(v, res[k]))
                res[k] = _deep_merge(res.get(k) or {}, v)
                continue
            res[k] = v
    return res


def simple_order(descending=False):
    return {'order': {'ID': 'DESC' if descending else 'ASC'}}


def voximplant_statistic_order(descending=False):
    return {'order': 'DESC' if descending else 'ASC', 'sort': 'ID'}


# Как выглядят параметры сортировки, у большинства: {'order': {'ID': 'DESC'}}
METHOD_TO_ORDER = {
    'tasks.task.list': simple_order,

    'crm.deal.list': simple_order,
    'crm.lead.list': simple_order,
    'crm.contact.list': simple_order,
    'crm.company.list': simple_order,

    'crm.product.list': simple_order,
    'crm.productrow.list': simple_order,
    'crm.activity.list': simple_order,

    'crm.requisite.list': simple_order,

    'voximplant.statistic.get': voximplant_statistic_order,

    # TODO:  в этот и прочие словари надо добавлять описания прочих методов,
    #   скорее всего достаточно будет скопировать то что сейчас описано
    #   для crm.deal.list. НО не надо добавлять сюда методы, которые 100%
    #   не работают, например user.get (не умеет фильтрацию >ID или <ID)
}


def filter_id_upper(
    index,  # type: int
    last_id=None,  # type: Optional[int]
    wrapper=None,  # type: Optional[str]
    descending=False,
):
    cmp = '<' if descending else '>'
    prop = cmp + 'ID'
    if index == 0:
        if last_id is not None:
            return {'filter': {prop: last_id}}
        return {}
    path = '$result[req_%d]' % (index - 1)
    if wrapper:
        path += '[%s]' % wrapper
    return {'filter': {prop: '%s[49][ID]' % path}}


def filter_id_mixed(
    index,  # type: int
    last_id=None,  # type: Optional[int]
    wrapper=None,  # type: Optional[str]
    descending=False,
):  # У задач в результате `id`, а в запросе `ID`
    cmp = '<' if descending else '>'
    prop = cmp + 'ID'
    if index == 0:
        if last_id is not None:
            return {'filter': {prop: last_id}}
        return {}
    path = '$result[req_%d]' % (index - 1)
    if wrapper:
        path += '[%s]' % wrapper
    return {'filter': {prop: '%s[49][id]' % path}}


# Как выглядят параметры фильтра, у большинства: {'filter': {'>ID': ...}}
METHOD_TO_FILTER = {
    'tasks.task.list': filter_id_mixed,

    'crm.deal.list': filter_id_upper,
    'crm.lead.list': filter_id_upper,
    'crm.contact.list': filter_id_upper,
    'crm.company.list': filter_id_upper,

    'crm.product.list': filter_id_upper,
    'crm.productrow.list': filter_id_upper,
    'crm.activity.list': filter_id_upper,

    'crm.requisite.list': filter_id_upper,

    'voximplant.statistic.get': filter_id_upper,
}


# Получить ID из сущности, у большинства `entity['ID']` или `entity['id']`
METHOD_TO_ID = {
    'tasks.task.list': itemgetter('id'),

    'crm.deal.list': itemgetter('ID'),
    'crm.lead.list': itemgetter('ID'),
    'crm.contact.list': itemgetter('ID'),
    'crm.company.list': itemgetter('ID'),

    'crm.product.list': itemgetter('ID'),
    'crm.productrow.list': itemgetter('ID'),
    'crm.activity.list': itemgetter('ID'),

    'crm.requisite.list': itemgetter('ID'),

    'voximplant.statistic.get': itemgetter('ID'),
}


# Большинство методов возвращают просто список, но некоторые
# (в основном у задач) имеют доп. обертку (например resp['result']['tasks'])
METHOD_TO_WRAPPER = {
    'tasks.task.list': 'tasks',
}


def call_list_fast(
    tok,  # type: BitrixUserToken
    method,  # type: str
    params=None,  # type: Dict[str, Any]
    descending=False,  # type: bool
    log_prefix='',  # type: str
    timeout=DEFAULT_TIMEOUT,  # type: Optional[int]
    limit=None,  # type: Optional[int]
    batch_size=50,  # type: int
):  # type: (...) -> Iterable[Any]
    """Быстрое получение списочных записей
    с помощью batch method?start=-1
    https://dev.1c-bitrix.ru/rest_help/rest_sum/start.php

    Производительность на 10к записях контактов CRM ~25 секунд против
    ~60 обычным списочным методом.

    Если записей мало (менее 2500) может оказаться медленнее.

    (Проверено) Работает с методами crm, пока не работает с `tasks.task.*`,
    другие методы не проверял. `tasks.task.list` просто игнорирует start=-1,
    результат возвращется корректный, но ускорения никакого.
    `user.get` игнорирует фильтр >ID и возвращает записи без фильтрации.

    Некоторые методы игнорируют фильтрацию вида `{'>ID': ...}`,
    например `user.get`, так что им этод метод не подойдет.

    TODO: заполнить справочники METHOD_TO_* при использовании прочих методов

    Usage:
        >>> but = BitrixUserToken.objects.filter(is_active=True).first()
        >>> for contact in but.call_list_fast('crm.contact.list'):
        >>>     print(contact['ID'], contact['NAME'], contact['LAST_NAME'])

    Возвращаемое значение (генератор) можно проитерировать (только 1 раз),
    альтернативно можно собрать в список:
        >>> deals = list(but.call_list_fast('crm.deal.list'))
    """

    ilogger.debug(
        'deprecated_fast_call', 'Используйте integration_utils.bitrix24.functions.call_list_fast.call_list_fast'
    )

    order_fn = METHOD_TO_ORDER[method]  # type: Callable[[bool], Dict[str, Any]]
    filter_fn = METHOD_TO_FILTER[method]  # type: Callable[[int, Optional[int], Optional[str], bool], Dict[str, Any]]
    id_fn = METHOD_TO_ID[method]  # type: Callable[[Any], Hashable]
    wrapper = METHOD_TO_WRAPPER.get(method)  # type: Optional[str]
    assert 1 <= batch_size <= 50
    assert limit is None or limit >= 0

    last_entity_id = None
    seen_ids = set()

    order_by = order_fn(descending)
    if params and any(key in order_by for key in params):
        raise ValueError("Method doesn't support sort/order")

    while True:
        batch_params = []
        for i in range(batch_size):
            # Необходимые методу параметры: фильтрация, сортировка, ?start=-1
            call_fast_params = _deep_merge(
                order_by,
                filter_fn(i, last_entity_id, wrapper, descending),
                dict(start=-1),
            )

            # Проверка нет ли параметров в разном регистре,
            # например filter и FILTER, из-за них бывают глюки
            check_lower_keys = set(key.lower() for key in call_fast_params)
            if params is not None and any(
                    (key not in call_fast_params and
                     key.lower() in check_lower_keys)
                    for key in params
            ):
                raise ValueError(
                    'Переданные параметры {params!r} могут конфликтовать '
                    'c параметрами метода {call_fast_params!r}. Проверьте, '
                    'чтобы регистр совпадал, например разный регистр filter и '
                    'FILTER вызвал баг на одном из порталов.'.format(**locals())
                )
            batch_params.append((
                'req_%d' % i,
                method,
                _deep_merge({} if params is None else params, call_fast_params),
            ))
        batch = tok.batch_api_call_v3(batch_params,
                                      timeout=timeout, log_prefix=log_prefix)
        for _, response in batch.iter_successes():
            result = response['result']
            if wrapper is not None:
                result = result[wrapper]
            # ilogger.debug('fast_batch_debug', "результат ".format(', '.join(id_fn(x) for x in result)))
            for entity in result:
                id = id_fn(entity)
                if id in seen_ids:
                    return  # Если встречается дубль - завершаем выполнение
                yield entity
                seen_ids.add(id)
                last_entity_id = id
                if limit is not None and len(seen_ids) >= limit:
                    return  # Достигли запрошенного лимита
        if not batch.all_ok:
            if (
                    method == 'voximplant.statistic.get' and
                    list(batch.errors.values())[0]['error_description'] == 'SQL query error!'
            ):  # fixme: количество методов в батче берётся с запасом. voximplant.statistic.get с сортировкой по
                #        убыванию при выходе батча за границы начинает отдавать 'SQL query error'. здесь мы уже
                #        получили все элементы, поэтому можем игнорировать ошибку
                return

            raise BatchApiCallError(batch)
        if not all(
                chunk['result'] and len(
                    chunk['result'][wrapper]
                    if wrapper
                    else chunk['result']
                ) == 50
                for chunk in batch.values()
        ):
            # Вернулся пустой список или менее 50 записей на один из запросов
            return
