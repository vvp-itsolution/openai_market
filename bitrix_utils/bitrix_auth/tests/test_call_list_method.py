import threading
import time

from bitrix_utils.bitrix_auth.models import BitrixUserToken

but = BitrixUserToken(web_hook_auth='1/einxq23hxcmi25e1', domain='b24-7r3aka.bitrix24.ru')



def create_deals(count=100, sleep=0):
    for i in range(0, count):
        if sleep:
            time.sleep(sleep)
        deal_id = but.call_api_method('crm.deal.add', {"TITLE": "Лид {}".format(i)}).get('result')
        if sleep:
            print("Создана сделка {}".format(deal_id))


def test_call_list():

    #Получаем 10000 сделок
    limit = 2500

    #Получаем последние созданные сделки в обратном порядке
    deals = but.call_list_method_v2(
        'crm.deal.list',
        {
            'select': "*",
            'order': {'ID': 'DESC'}
        },
        limit, timeout=300)

    print("Нужно было плучить 2500, получено {}".format(len(deals)))

    # В отдельном потоке созадем сделки снова
    threading.Thread(target=create_deals, kwargs={"count": 30, "sleep": 0.2}).start()

    # и теперь смещение должно мешать колл лист методу должны по два раза айдишинки попадать
    print("======================================")
    print("Загружкаем последние добавленные сделки 'order': {'ID': 'DESC'}")
    deals = but.call_list_method_v2(
        'crm.deal.list',
        {
            'select': "*",
            'order': {'ID': 'DESC'}
        },
        limit, timeout=300)

    print("Нужно было плучить 2500, получено {}".format(len(deals)))
    deals = set([x["ID"] for x in deals])
    print("А уникальных ID {}".format(len(deals)))

    print("======================================")
    print("А теперь id в прямом порядке 'order': {'ID': 'ASC'}")
    # и теперь смещение должно мешать колл лист методу должны по два раза айдишинки попадать
    deals = but.call_list_method_v2(
        'crm.deal.list',
        {
            'select': "*",
            'order': {'ID': 'ASC'}
        },
        limit, timeout=300)

    print("Нужно было плучить 2500, получено {}".format(len(deals)))
    deals = set([x["ID"] for x in deals])
    print("А уникальных ID {}".format(len(deals)))
