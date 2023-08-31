from django.conf import settings

from bitrix_utils.bitrix_auth.models import BitrixUserToken


def firststeps(butname, nav=''):

    res = {}
    menu = {}

    but = BitrixUserToken.objects.get(pk=settings.BITRIX_USER_TOKENS_MAP[butname])
    print("Передан токен {} для приложения {}  и мы его нашли {}".format(butname, but.application, but))
    print("Список приложений и вебхуков https://{}/devops/list/".format(but.user.portal.domain))

    if nav == '':
        res['lists'] = but.call_list_method('lists.get', {"IBLOCK_TYPE_ID": "lists"})
        menu['lists'] = [{"list_{}".format(x['ID']): x['NAME'] } for x in  res['lists']]
        res['bitrix_processes'] = but.call_list_method('lists.get', {"IBLOCK_TYPE_ID": "bitrix_processes"})

    if nav.startswith('list_'):
        list_id = nav.split('list_')[1]
        res['lists.get'] = but.call_list_method('lists.get', {"IBLOCK_TYPE_ID": "lists", "IBLOCK_ID":list_id})
        res['lists.field.get'] = but.call_list_method('lists.field.get', {"IBLOCK_TYPE_ID":"lists", "IBLOCK_ID":list_id})



    return but, res, menu