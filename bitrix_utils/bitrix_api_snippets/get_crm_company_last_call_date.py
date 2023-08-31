# -*- coding: utf-8 -*-

from bitrix_utils.bitrix_auth.models import BitrixUserToken
from bitrix_utils.bitrix_api_snippets.get_crm_company_entities import get_crm_company_entities

import six

if not six.PY2:
    from typing import Optional, List, Union, Sequence


def get_crm_company_last_call_date(
        bitrix_user_token,  # type: BitrixUserToken
        company_id,  # type: int
        call_type=None,  # type: Optional[int]
        min_call_duration=None,  # type: Optional[int]
):  # type: (...) -> Optional[str]
    """
    Получить дату последнего успешного звонка компании

    :param bitrix_user_token: токен
    :param company_id: id компании
    :param call_type: направление звонка (1 - исходящий, 2 - входящий, None - любой)
    :param min_call_duration: минимальная длительность звонка
    :return: iso-дата последнего звонка или None
    """

    # получить связанные с компанией сущности
    crm_entities = get_crm_company_entities(bitrix_user_token, company_id)

    # получить даты последних успешных звонков для всех сущностей
    last_call_date_list = []
    for (crm_entity_type, crm_entity_id) in crm_entities.items():
        if not crm_entity_id:
            continue

        last_call_date = _get_last_call_date(
            bitrix_user_token,
            crm_entity_type,
            crm_entity_id,
            call_type,
            min_call_duration,
        )

        if last_call_date:
            last_call_date_list.append(last_call_date)

    # взять самую позднюю из дат или None, если не нашли звонков
    return max(last_call_date_list) if last_call_date_list else None


def _get_last_call_date(
        bitrix_user_token,  # type: BitrixUserToken
        crm_entity_type,  # type: str
        crm_entity_id,  # type: Union[int, Sequence[int]]
        call_type=None,  # type: Optional[int]
        min_call_duration=None,  # type: Optional[int]
):  # type: (...) -> Optional[str]
    """
    Получить дату последнего успешного звонка сущности crm

    :param bitrix_user_token: токен
    :param crm_entity_type: тип сущности (COMPANY|CONTACT|DEAL|LEAD)
    :param crm_entity_id: id сущности или список id
    :param call_type: тип звонка (1 - исходящий, 2 - вхоядщий, None - любой)
    :param min_call_duration: минимальная длительность звонка
    :return: iso-дата последнего звонка или None
    """

    filter_ = {
        'CRM_ENTITY_TYPE': crm_entity_type,
        'CRM_ENTITY_ID': crm_entity_id,
    }

    if min_call_duration:
        filter_['>=CALL_DURATION'] = min_call_duration

    if call_type:
        filter_['CALL_TYPE'] = call_type

    calls = bitrix_user_token.call_api_method('voximplant.statistic.get', {
        'FILTER': filter_,
        'SORT': 'CALL_START_DATE',
        'ORDER': 'desc',  # первый в списке - последний звонок
    })['result']

    if calls:
        return calls[0]['CALL_START_DATE']

    return None
