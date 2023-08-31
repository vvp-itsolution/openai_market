
Модель BitrixChatBot является абстрактной, на базе ее можно создать бота в Б24.
Каждая запись в базе данных будет отражать одного установленного бота на каком-либо портале




### Как прописать urls
from django.conf.urls import url

from test_bitrix_bot.models.test_bot import TestBot

urlpatterns = [
    url(r'^register_bot/', TestBot.register_view),
    url(r'^unregister_bot/', TestBot.unregister_view),
    url(r'^event/', TestBot.event_view),
]
