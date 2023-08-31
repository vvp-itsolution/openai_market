from its_utils.app_logger.models.abs_log_record import AbsLogRecord
from its_utils.functions import datetime_to_string


class BitrixChatBotEventLog(AbsLogRecord):
    bot = None  # models.ForeignKey('BitrixChatBot', null=True, blank=True, on_delete=models.CASCADE)

    from its_utils.django_postgres_fuzzycount.fuzzycount import FuzzyCountManager
    objects = FuzzyCountManager()

    class Meta:
        abstract = True

    def __str__(self):
        return 'record {}'.format(self.id)

    @property
    def pretty_message(self):
        return (
            u'[{}][{}]({})({})({})\n'
            u'portal: {}\n'
            u'{}\n'
            u'{}'.format(
                self.type, self.get_level_display(), self.script, self.lineno, datetime_to_string(self.date_time),
                self.bot,
                self.message,
                self.exception_info
            )
        )

    def before_save(self):
        if type(self.params) is dict:
            self.bot_id = self.params.get('bot_id')
