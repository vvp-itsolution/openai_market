### Описание
Приложение хранит bitrix-порталы и их пользователей.

### Установка

1. **Прежде всего нужно добавить submodule git'а - its_utils и настроить app_logging**
1. Для корректной работы в settings.py необходимо добавить следующие параметры:
    1. `BITRIX_CLIENT_ID` = 'app.313123e23123123.312312' - Код приложения (client_id)
    1. `BITRIX_CLIENT_SECRET` = 'a3MSyes33sTcUNCaRqHRcL4ckcsYxfR6' - Секретный ключ (client_secret)
    1. `BITRIX_SCOPE` = 'log,user' - Список полномочий приложения
    1. `BITRIX_REDIRECT_URL` = 'https://...' - URL проекта
    1. `SALT` = 'tUmU2uPwY2jtLrRU8rfxpQJR47QCaYkbXrfYrCs57bDaaesABNL2Knh3E9ChHMPnYWDdGGdPDVwYu7aSHgJrrk5vTUhVtqNRSCDsyUKJek7qCpZ' - Набор символов для создания ключей аутентификации. Лучший спосок сгенерировать такую последовательность - `User.objects.make_random_password(255)`
1. А также добавить `'bitrix_utils.bitrix_auth',` в INSTALLED_APPS.

### Использование
Чтобы порталы и пользователи добавлялись автоматически, необходимо поставить декоратор `bitrix_utils.bitrix_auth.functions.bitrix_start_point` на view - точку входа приложения.
Также необхожимо доавбить декоратор `@csrf_exempt`, так как от bitrix'a приходит POST запрос.

Если все настроено правильно, в `request` появятся следующие поля: 

1. `request.bx_user_is_new` - создан новый пользователь или взят уже имеющийся
1. `request.bx_auth_key` - ключ для добавления в HTTP загловок для аутентификации
1. `request.bx_user` - объект модели BitrixUser

В стартовый html-шаблон можно вставить код вида:

```
{% if user %}
    <script>
        window.user = {
            id: {{ user.id }},
            lastName: "{{ user.last_name }}",
            firstName: "{{ user.first_name }}",
            token: "{{ bx_auth_key }}"
        };

        {% if user.is_admin %}
            window.user.isAdmin = true;
        {% endif %}
    </script>
{% endif %}
```

Тогда на клиенте можно обращаться к полям пользователя через JS.

Также, для прохождения авторизации необходимо добавлять HTTP-заголовок 'Authorization' к каждому запросу. В Angular'е

###Примечание

* Для корректной работы django-проекта в iframe необходимо убрать `'django.middleware.clickjacking.XFrameOptionsMiddleware',` из `MIDDLEWARE_CLASSES`
* Также в settings.py в `STATICFILES_DIRS` можно добавить `os.path.join(BASE_DIR, 'bitrix_utils', 'static'),` тогда можно будет использовать стили bitrix'a
* Для корректного отображения JSONField в админке требуется установить
    `django-prettyjson` и добавить `'prettyjson'` в `settings.INSTALLED_APPS`
