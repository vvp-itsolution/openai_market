# -*- coding: utf-8 -*-

from bitrix_utils.bitrix_auth.models import BitrixUserToken

import six

if not six.PY2:
    from typing import List


def get_crm_company_entities(
        bitrix_user_token,  # type: BitrixUserToken
        company_id,  # type: int
):  # type: (...) -> List[tuple]
    """
    Получить id сущностей, связанных с компанией

    :param bitrix_user_token: токен
    :param company_id: id компании
    :return: словарь {<тип сущности>: [<список id>]}
    """

    # получить id всех лидов, привязанных к компании
    leads = bitrix_user_token.call_list_method_v2('crm.lead.list', {
        'filter': {'COMPANY_ID': company_id},
        'select': ['ID']
    })
    lead_ids = list({c['ID'] for c in leads})

    # получить id всех контактов компании
    contacts = bitrix_user_token.call_list_method_v2('crm.contact.list', {
        'filter': {'COMPANY_ID': company_id},
        'select': ['ID']
    })
    contact_ids = list({c['ID'] for c in contacts})

    # получить id всех сделок компании
    company_deals = bitrix_user_token.call_list_method_v2('crm.deal.list', {
        'filter': {'COMPANY_ID': company_id},
        'select': ['ID']
    })
    deal_ids = {d['ID'] for d in company_deals}

    if contact_ids:
        # получить id всех сделок контактов компании
        contact_deals = bitrix_user_token.call_list_method_v2('crm.deal.list', {
            'filter': {'CONTACT_ID': contact_ids},
            'select': ['ID']
        })
        deal_ids |= {d['ID'] for d in contact_deals}

    deal_ids = list(deal_ids)

    return {
        # компании
        'COMPANY': [company_id],

        # привязанные лиды
        'LEAD': lead_ids,

        # контакты компании
        'CONTACT': contact_ids,

        # сделки контактов и компании
        'DEAL': deal_ids,
    }
