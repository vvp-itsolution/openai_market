##Документация (не работает с django 1.6)

###Установка


1. `pip install -r requirements.txt`

2. В `settings.py` добавить
```
INSTALLED_APPS = (
    ...,

    'its_utils.app_documentation',
)
```


3. в urls.py
`url(r'^its/docs/', include('its_utils.app_documentation.urls')),`
