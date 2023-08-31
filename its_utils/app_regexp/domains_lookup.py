import re

from its_utils.app_regexp.constants import REGEXP_DOMAIN, REGEXP_DOMAIN_V2


def is_domain(text, domains_v2=False):
    if domains_v2:
        if not re.fullmatch(REGEXP_DOMAIN_V2, text):
            return False
    else:
        if not re.fullmatch(REGEXP_DOMAIN, text):
            return False
    return True