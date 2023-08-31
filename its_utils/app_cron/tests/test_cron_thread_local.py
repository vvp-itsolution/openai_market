import time

from its_utils.app_cron.cron_thread_local import append_cron_result


def test_cron_thread_local():
    # Функция которая должна в результаты крона писать во время выполнения
    for i in range(1, 30):
        append_cron_result('Итерация {}'.format(i))
        time.sleep(1)