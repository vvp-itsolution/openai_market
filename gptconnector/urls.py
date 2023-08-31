from django.urls import path

from gptconnector.views.handle_request import handle_request
from gptconnector.views.index import index
from gptconnector.views.process_tasks import process_tasks
from gptconnector.views.register_engine import register_engine
from gptconnector.views.save_api_key import save_api_key
from gptconnector.views.unregister_engine import unregister_engine

app_name = 'gptconnector'

urlpatterns = [
    path('', index),
    path('save_api_key/', save_api_key, name='save_api_key'),
    path('handle_request/', handle_request, name='handle_request'),
    path('register_engine/', register_engine, name='register_engine'),
    path('unregister_engine/', unregister_engine, name='unregister_engine'),
    path('process_tasks/', process_tasks, name='process_tasks'),
]
