import threading

import requests

MAX_MESSAGE_LENGTH = 4096


def post_to_telegram_async(chat_id, message, parse_mode='HTML', concat_id=None):
    threading.Thread(target=post_to_telegram,
                     args=[chat_id, message],
                     kwargs={'parse_mode': parse_mode, 'concat_id': concat_id}).start()
    return


def post_to_telegram(chat_id, message, parse_mode='HTML', concat_id=None):
    # https://ts.it-solution.ru/#/ticket/59906/
    # if len(message) > MAX_MESSAGE_LENGTH:
        # message = '{}...'.format(message[:MAX_MESSAGE_LENGTH - 3])
    # 2022-07-18 убрал это, сделал разбиение длинных сообщений на стороне telegram-client.it-solution.ru

    if type(chat_id) == str and not chat_id.lstrip('-').isdigit():
        # Можно укзалть либо id чата, лбо название приложения для логов из /admin/app_logger/loggedapp/
        from its_utils.app_logger.models import LoggedApp
        chat_id = int(LoggedApp.objects.get(name=chat_id).telegram_chat)

    params = {
        'chat_id': chat_id,
        'message': message
    }

    if parse_mode:
        params['parse_mode'] = parse_mode

    if concat_id:
        params['concat_id'] = concat_id

    response = requests.post('https://telegram-client.it-solution.ru/pub_message/', params)
    if response.status_code not in [200, 420]:
        requests.post('https://telegram-client.it-solution.ru/pub_message/',
                     {'chat_id': chat_id, 'message': 'Не отправилось {} {}'.format(response.status_code, response.content)})
        requests.post('https://telegram-client.it-solution.ru/pub_message/',
                     {'chat_id': chat_id, 'message': message})

    return response
