Простейший режим использования
-----------

1) Добавить в **INSTALLED_APPS**  'its_utils.app_logger'
2) Создать таблицы в БД   `migrate`
3) Использование в коде
~~~~
from its_utils.app_logger.its_logger import ItsLogger
ItsLogger().info('test_log_type', 'test log message')
~~~~
4) Просмотр событий в админке по урл /admin/app_logger/logrecord/

Добавление ilogger в settings
--------------
Для красоты исползуется такой вариант
в файл settings.py добавляется
~~~~
from its_utils.app_logger.its_logger import ItsLogger
ilogger = ItsLogger()
~~~~

в остальном проекте можно использовать чуть короче
~~~~
from settings import ilogger
ilogger.debug('test_log_type', 'test log message')
~~~~

##Усложенный режим: создание нового класса логерра
Если мы хотим добавить доп поле для логгера, то придется создать отдельный класс

1) создаем прилжение separate_logger и добавляем в INSTALLED_APPS
2) Создаем модель и добавляем дополнительные поля, и правило их заполенния в before_save по желанию pretty_message
class SeparateRecord(AbsLogRecord):
    portal = models.ForeignKey('bitrix_auth.BitrixPortal', null=True, blank=True, on_delete=models.CASCADE)
    device = models.ForeignKey('smsbanan.Device', null=True, blank=True, on_delete=models.CASCADE)

    @property
    def pretty_message(self):
        return (
            u'[{}][{}]({})({})({})\n'
            u'portal: {}\n'
            u'{}\n'
            u'{}'.format(
                self.type, self.get_level_display(), self.script, self.lineno, datetime_to_string(self.date_time),
                self.portal,
                self.message,
                self.exception_info
            )
        )

    def before_save(self):
        if type(self.params) is dict:
            self.portal_id = self.params.get('portal_id')
            self.device_id = self.params.get('device_id')

3) Делаем миграции
4) Добавляем админку
5) Добавляем крон its_utils.app_logger.functions.cron.process_log_records
с параметрами {"last_log_id_key":"Здесь надо придумать имя переменной для хранения последней отправленной записи", "record_model":"SeparateRecord")}
6) добавить в сеттинги например,
separate_logger = ItsLogger(app='separate_logger', record_model=SeparateRecord)
7) использовать как обычный логгер но добавлять ПАРМЕТРЫ
separate_logger.info('kuku', 'kuku', params=dict(portal_id=request.sms_token.bx_portal_id))

