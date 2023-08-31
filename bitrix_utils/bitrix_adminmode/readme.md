# bitrix_adminmode

###Настройки

myapp/admin_mode_settings.py
```python
from bitrix_utils.bitrix_adminmode.admin_mode_settings import AdminModeSettings
from myapp.views.admin_hello import AdminHello

admin_mode_settings = AdminModeSettings(
    app_name='myapp',  # имя приложения должно совпадать с app_name в urls.py
    application_codes=['itsolutionru.myapp'],  # коды приложений для bitrix_auth_required
    title='Моё приложение',  # заголовок
    extra_view_classes=[AdminCache],  # доплнительные вкладки
)
```

myapp/urls.py
```python
# ...
from myapp.admin_mode_settings import admin_mode_settings

app_name = 'myapp'

urlpatterns = [
    # ...
    path('adminmode/', include(admin_mode_settings.urls())),
    # ...
] 
```

###Дополнительные вкладки
myapp/views/admin_hello.py
```python
from its_utils.app_get_params.functions import int_param
from bitrix_utils.bitrix_adminmode.admin_mode_view import AdminModeView
from bitrix_utils.bitrix_adminmode.admin_mode_view_param import AdminModeViewParam


class AdminCache(AdminModeView):
    VIEW_NAME = 'hello'
    TITLE = 'Приветствие'
    TEMPLATE_NAME = 'myapp/admin/hello.html'

    PARAMS = dict(
        number=AdminModeViewParam(coerce=int_param, default=16),
    )

    def get_context(self, request, params):
        return dict(
            name=request.bx_user.display_name,
            number=params['number'],
        )
```

myapp/admin/hello.html
```djangotemplate
{% extends 'bitrix_adminmode/base.html' %}

{% block content %}
  <p>Привет, {{ name }}! Твой номер {{ number }}.</p>
{% endblock %}

```


###Логирование
```python
from myapp.admin_mode_settings import admin_mode_settings

logger = admin_mode_settings.get_portal_logger(portal=bitrix_portal)

logger.debug('debug_log_type', 'debug log message...')
logger.warning('warning_log_type', 'warning log message...')
```


###Ограничение количество записей лога для портала
https://b24.it-solution.ru/workgroups/group/421/tasks/task/view/7571/

settings.py
```python
PORTAL_LOG_LIMIT = 5000  # по умочанию 1000
```