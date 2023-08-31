import re

from its_utils.app_regexp.constants import REGEXP_DOMAIN_V2, REGEXP_DOMAIN

TEST_DOMAINS = """
mail.ru
https://ya.ru
ya.ru,mail.ru,google.com
,ya.ru,mail.ru,google.com
ya.ru|mail.ru|google.com
it-solution.ru
ma.sa.it-solution.ru
ma-11.s-a.it-solution.ru
img@it-solution.ru
127.0.0.1
333.444
script.py
nginx.conf
hello@google.com
evg.com@google.com
evg.com@google.comaa
script.js
12345 -98.7 3.141 .6180 9,000 +42
evg.com@
"""


def test_domains_list():
    for domain in TEST_DOMAINS.split('\n'):
        if not domain:
            continue

        domains = re.findall(REGEXP_DOMAIN, domain)
        domainsv2 = re.findall(REGEXP_DOMAIN_V2, domain)
        print(domain, domains, domainsv2)
