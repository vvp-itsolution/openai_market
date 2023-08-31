import datetime
import pytz
CRON_STARTED = datetime.datetime.now(pytz.utc)


import multiprocessing
import os
import sys
import threading
import time



FILE_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(FILE_PATH, '../../'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')


import django
from django.utils import timezone

# django.setup() требуется только для версий django >=1.7
try:
    django.setup()
except AttributeError:
    # чит, чтобы сделать импорт сеттинг для версии 1.6
    from django.conf import settings

    _ = settings.LOGGING

from its_utils.functions import is_date_in_cronstring


# from ticks.models import Entry
from its_utils.app_cron.models import Cron, CronResult, CronLog

from its_utils.app_cron.functions.clean_logs import check_datetime_and_clean_logs

COUNT = 60
DELAY = 1
CRON_KEY = 'cron_%s'
API_KEY = 123123
TICKET_ID = 19718  # https://ts.it-solution.ru/#/ticket/19718/

#CRON_STARTED = settings.DJANGO_STARTEDtimezone.now()
#from django.conf import settings
#CRON_STARTED = getattr(settings, 'DJANGO_STARTED', timezone.now())

MAX_UNFINISHED_TASKS_PER_MESSAGE = 100

def process_repeat_seconds_crons(tick, cache_key, crons, cron_log_id, multiprocesses):
    print(cache_key, tick)
    tick += 1
    if tick <= COUNT:
        threading.Timer(DELAY, process_repeat_seconds_crons, args=[tick, cache_key, crons, cron_log_id, multiprocesses]).start()

        for cron in crons:
            # Тики от 1 до 60 и остаток от деления корректируем на -1
            if (tick - 1) % cron.repeat_seconds == 0:
                if cron.is_ready_to_start():
                    t = threading.Thread(target=cron.eval_cron, args=[cron_log_id])
                    #p = multiprocessing.Process(target=cron.eval_cron, name=CRON_KEY % cron.id, args=[cron_log_id])
                    multiprocesses.append({
                        'process': t,
                        'start_time': timezone.now(),
                        'cron': cron,
                    })
                    t.start()

    else:
        print('%s stopped' % cache_key)


def process_usual_crons(crons, cron_log_id, multiprocesses, cron_started_time):
    for cron in crons:
        if cron.is_ready_to_start():
            if is_date_in_cronstring(cron_started_time, cron.string):
                t = threading.Thread(target=cron.eval_cron, args=[cron_log_id])
                #p = multiprocessing.Process(target=cron.eval_cron, name=CRON_KEY % cron.id, args=[cron_log_id])
                multiprocesses.append({
                    'process': t,
                    'start_time': timezone.now(),
                    'cron': cron,
                })
                t.start()


def check_unfinished_tasks():
    """
    Найти процессы, которые выполняются дольше часа, отправить оповещения
    """

    for cron in Cron.objects.all():
        cron.check_unfinished_tasks()


def main():
    from settings import ilogger
    from its_utils.app_admin.get_admin_url import get_admin_a_tag
    multiprocessing.set_start_method('spawn')
    try:
        process = sys.argv[1]
    except IndexError:
        process = 1

    try:
        process = int(process)
    except ValueError:
        print('Bad process parameter', file=sys.stderr)
        sys.exit()
    cron_log = CronLog(started=CRON_STARTED, process=process)
    cron_log.save()
    crons = Cron.objects.filter(active=True, process_filter=process)

    multiprocesses = []

    # несколько раз в минуту, выполняется рекурсивно, поэтому почти не блокирует поток выполнения
    if crons.filter(repeat_seconds__isnull=False).count():
        process_repeat_seconds_crons(tick=0, cache_key='app_cron_%s' % process,
                                 crons=crons.filter(repeat_seconds__isnull=False), cron_log_id=cron_log.id, multiprocesses=multiprocesses)

    # раз в минуту
    process_usual_crons(crons.filter(repeat_seconds__isnull=True), cron_log.id, multiprocesses, cron_started_time=CRON_STARTED)

    try:
        check_unfinished_tasks()
    except Exception as exc:
        print('check_unfinished_tasks failed: {}'.format(exc))

    check_datetime_and_clean_logs(datetime=CRON_STARTED)

    time.sleep(60)
    print(multiprocesses)

    while len(multiprocesses):
        live = []
        for m in multiprocesses:
            if not m['process'].is_alive():
                # Кончился процесс
                m['process'].join()
            else:
                if m['start_time'] + timezone.timedelta(seconds=m['cron'].timeout) <= timezone.now():
                    ilogger.warning('cron_timeout', "{}".format(get_admin_a_tag(m['cron'])))
                ilogger.debug('cron_wait', "{}".format(get_admin_a_tag(m['cron'])))
                print('run {} sec'.format((timezone.now()-m['start_time']).seconds))
                live.append(m)

        multiprocesses = live
        if len(multiprocesses):
            time.sleep(10)

    cron_log.stopped = timezone.now()
    cron_log.finished = True
    cron_log.save()


if __name__ == '__main__':
    main()
