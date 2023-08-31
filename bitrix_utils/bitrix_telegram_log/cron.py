from bitrix_utils.bitrix_telegram_log.models import TelegramLogBot
from settings import ilogger


def handle_bot_updates():
    from integration_utils.vendors.telegram.vendor.ptb_urllib3 import urllib3
    urllib3.disable_warnings()

    results = []
    for bot in TelegramLogBot.objects.filter(is_active=True):
        try:
            replies_count, command_count, fails_count = bot.handle_updates()
            result = 'updates handled: {}, commands handled: {}, commands failed: {}'.format(
                replies_count, command_count, fails_count
            )

        except Exception as exc:
            ilogger.error('handle_telegram_log_bot_updates', '{}: {}'.format(bot, exc))
            result = 'Error! {}'.format(exc)

        results.append('{}: {}'.format(bot, result))

    return '\n'.join(results)
