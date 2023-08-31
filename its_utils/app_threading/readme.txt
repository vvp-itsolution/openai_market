import threading


def start_post_to_telegram_in_thread(chat_id, message, parse_mode, concat_id):
    threading.Thread(target=post_to_telegram,
                     args=[chat_id, message],
                     kwargs={'parse_mode': parse_mode, 'concat_id': concat_id}).start()
    return