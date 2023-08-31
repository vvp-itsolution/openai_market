import re
from its_utils.app_regexp.constants import REGEXP_DOMAIN, EXCLUDE_DOMAINS, REGEXP_VK_ENTITY, REGEXP_TG_ENTITY, \
    REGEXP_EMAIL, REGEXP_PHONE_V2, REGEXP_DOMAIN_V2


def find_contacts_in_text(text, return_dict=False, domains_v2=False):
    phones = re.findall(REGEXP_PHONE_V2, text)
    emails = re.findall(REGEXP_EMAIL, text)

    if domains_v2:
        domains = re.findall(REGEXP_DOMAIN_V2, text)
    else:
        domains = re.findall(REGEXP_DOMAIN, text)
    domains = list(set(domains) - set(EXCLUDE_DOMAINS) - set([x.split('@')[1] for x in emails]))

    vk_entities = re.findall(REGEXP_VK_ENTITY, text)
    tg_entities = re.findall(REGEXP_TG_ENTITY, text)

    if return_dict:
        return dict(
            phones=list(set(phones)),
            domains=list(set(domains)),
            emails=list(set(emails)),
            vk_entities=list(set(vk_entities)),
            tg_entities=list(set(tg_entities)),
        )

    return list(set(phones + emails + domains + vk_entities + tg_entities))