from django.db import models
from django.contrib import admin


class AbstractThread(models.Model):

    class Meta:
        abstract = True
        verbose_name = 'Ветка'
        verbose_name_plural = 'Ветки'

    telegram_id = models.CharField(max_length=100, null=True, blank=True)
    chat = models.ForeignKey('TelegramChat', on_delete=models.PROTECT)

    def __str__(self):
        return 'thread{}'.format(self.telegram_id)

    # def get_secret(self):
    #     if not self.secret:
    #         self.secret = get_random_string(20)
    #         self.save(update_fields=['secret'])
    #
    #     return self.secret
    #
    # def get_link(self):
    #     return 'https://web.telegram.org/#/im?p=g{}'.format(self.telegram_id)

    class Admin(admin.ModelAdmin):
        list_display = ['id', 'telegram_id', 'chat']
        list_display_links = list_display
        # inlines = ChatParticipantInline,
        search_fields = 'telegram_id',

    @classmethod
    def from_update(cls, update, bot, chat):
        if update.message:
            message_thread_id = update.message.message_thread_id

        elif update.callback_query:
            message_thread_id = update.callback_query.message.message_thread_id

        elif update.edited_message:
            message_thread_id = update.edited_message.message_thread_id

        else:
            return None

        thread, _ = cls.objects.get_or_create(telegram_id=message_thread_id, chat_id=chat.id)
        # thread.chat = chat
        # thread.save(update_fields=['chat',])

        return thread
