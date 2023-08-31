Подсказки при старте приложения, модели и API

### Установка:

- `pip install django-froala-editor`
- добавить в INSTALLED_APPS:
```py
INSTALLED_APPS = [
    # django apps...
    'froala_editor',
    'its_utils.app_tips_on_start',
    # my app...
]
```
- добавить в `urls.py`
```py
urlpatterns = [
    url(r'^froala_editor/', include('froala_editor.urls')),
    url(r'^its/tips/', include('its_utils.app_tips_on_start.urls')),
    # ... my patterns...
]
```
- Ключ для сайтов на домене `it-solution.ru` (в `settings.py`)
```py
FROALA_EDITOR_OPTIONS = dict(
    key='WE1B5dG3G4F3A6C9B5cWHNGGDTCWHIg1Ee1Oc2Yc1b1Lg1POkB6B5F5C4F3D3A2F2A5B3==',
)
```
