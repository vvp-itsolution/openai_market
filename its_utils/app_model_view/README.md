Просмотр таблиц БД. Достаточно добавить `'its_utils.app_model_view',` в INSTALLED_APPS и
` url(r'^its/model_view/', include('its_utils.app_model_view.urls')),` в urls.py и по адресу
/its/model_view/APP_NAME/MODEL_NAME можно посмотреть содержимое таблицы.


###Использует its_utils.app_converter, поэтому надо установить все его зависимости


