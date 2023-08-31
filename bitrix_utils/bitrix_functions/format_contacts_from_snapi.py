from bitrix_utils.bitrix_functions.get_object_title import get_object_title
from its_utils.app_telegram_bot.common import escape_html


LEAD = 'lead'
COMPANY = 'company'
CONTACT = 'contact'

TYPES_DISPLAY = {
    LEAD: 'Лид',
    COMPANY: 'Компания',
    CONTACT: 'Контакт',
}


def format_contacts_from_snapi(domain, contacts, skip_empty=True):
    # эта функция генерирует текст по результату полученному от https://snapi.it-solution.ru/api/crm.check_contacts/

    counter = 0
    results = []
    result = []
    empty = []
    for res in contacts:
        if not (skip_empty or any(res['result'].get(t.upper()) for t in TYPES_DISPLAY.keys())):
            empty.append('Искал <i>{}</i>, но не нашёл'.format(res['contact']))
            empty.append('')
            continue

        result.append('<i>{}</i>'.format(res['contact']))
        result.append('')

        found = False
        for bx_type, display in TYPES_DISPLAY.items():
            objects = res['result'].get(bx_type.upper())
            if objects:
                found = True
                for obj in objects:
                    result.append(
                        '<b>{display}</b> <a href="https://{domain}/crm/{type}/details/{id}/">{title}</a>'.format(
                            display=escape_html(display),
                            domain=domain,
                            type=bx_type,
                            id=obj['ID'],
                            title=escape_html(get_object_title(obj))
                        )
                    )

                    company = obj.get('COMPANY')
                    if company:
                        result.append(
                            'Компания: '
                            '<a href="https://{domain}/crm/company/details/{id}/">{title}</a>'.format(
                                domain=domain,
                                id=company['ID'],
                                title=escape_html(get_object_title(company))
                            )
                        )

                    user_xing_str = ''
                    if 'ASSIGNED_BY' in obj and 'UF_XING' in obj['ASSIGNED_BY']:
                        user_xing = obj['ASSIGNED_BY'].get('UF_XING', '')
                        if user_xing:
                            user_xing_str = ' ' + user_xing
                    result.append(
                        'Ответственный: <a href="https://{domain}/company/personal/user/{user_id}/">'
                        '{user_name}</a>{user_xing_str}'.format(
                            domain=domain,
                            user_id=obj['ASSIGNED_BY_ID'],
                            user_name=escape_html(get_object_title(obj['ASSIGNED_BY'])),
                            user_xing_str=user_xing_str
                        )
                    )

                    deals = obj.get('UNFINISHED_DEALS')
                    if deals:
                        result.append(
                            'Активные сделки:\n{}'.format('\n'.join([
                                '<a href="https://{domain}/crm/deal/details/{id}/">{title} ({user})</a>'.format(
                                    domain=domain, id=deal['ID'],
                                    title=escape_html(get_object_title(deal)),
                                    user=escape_html(get_object_title(deal['ASSIGNED_BY']))
                                ) for deal in deals
                            ]))
                        )

                    else:
                        result.append('Активных сделок нет')

                    result.append('')

        if not found:
            result.append('<i>Не найдено</i>')

        result.append('')
        counter += 1
        if counter == 1:  # Количество контактов в сообщении
            counter = 0
            results.append(result)
            result = []

    if len(result):
        results.append(result)

    return results, empty