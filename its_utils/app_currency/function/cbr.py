import requests

CBR_XML_BASE_URL = 'https://www.cbr-xml-daily.ru/'
EXCHANGE_RATE_JSON_URL = CBR_XML_BASE_URL + 'daily_json.js'
EXCHANGE_RATE_JSON_ARCHIVE_URL = CBR_XML_BASE_URL + 'archive/{date.year}/{date.month:02d}/{date.day:02d}/daily_json.js'


def get_exchange_rate():
    resp = requests.get(EXCHANGE_RATE_JSON_URL, timeout=10)
    if resp.ok:
        return resp.json()

    raise RuntimeError('[{}] {}'.format(resp.status_code, resp.text))


def get_exchange_rate_archive(date):
    resp = requests.get(EXCHANGE_RATE_JSON_ARCHIVE_URL.format(date=date), timeout=10)
    if resp.ok:
        return resp.json()

    if resp.status_code == 404:
        return None

    raise RuntimeError('[{}] {}'.format(resp.status_code, resp.text))
