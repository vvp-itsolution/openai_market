Это приложение для выполнения запросов к серверу приложения file_storage из других проектов

---------------------------------------------------------------------------------------------------

Перед тем как пользоваться необходимо заполнить в local_settings.py

FILE_STORAGE_SIGNER_SECRET = ''
такое же значение секретного ключа как в приложении file_storage

FILE_STORAGE_DOMAIN = ''
домен приложения file_storage

FILE_STORAGE_API_KEY = ''
api_key из UserSettings пользователя file_storage, который соответствует этому приложению
(например, пользователь "База Знаний")
https://fs.it-solution.ru/admin/file_storage/usersettings/

---------------------------------------------------------------------------------------------------

Пример отправки файла в хранилище:

import requests
from its_utils.app_file_storage.functions.add_file import add_file

file_from_internet_response = requests.get('https://ru.wikipedia.org/static/images/project-logos/ruwiki.png')

file_name = 'ruwiki.png'
file_content = file_from_internet_response.content

add_file_response = add_file(file_name, file_content).json()

if not add_file_response['error']:
    storage_file_id = add_file_response['file_id']
    storage_file_datetime_created = add_file_response['file_datetime_created']

    {{ далее сохраняем полученные storage_file_id и storage_file_datetime_created куда-нибудь чтобы потом по ним получать файл }}

ФОРМАТ УСПЕШНОГО РЕЗУЛЬТАТА add_file()
{
    'error': False,
    'file_id': 8,
    'file_datetime_created': '2021-08-09T19:50:59.283734+00:00'
}

---------------------------------------------------------------------------------------------------

Пример получения файла из хранилища:

import requests
from its_utils.app_file_storage.functions.get_file import get_file

# --- берем storage_file_id и storage_file_datetime_created оттуда где их сохранили ---
storage_file_id = 8
storage_file_datetime_created = '2021-08-09T19:50:59.283734+00:00'
# -------------------------------------------------------------------------------------

storage_file_data = get_file(storage_file_id, storage_file_datetime_created).json()

ФОРМАТ УСПЕШНОГО РЕЗУЛЬТАТА get_file()
{
    'error': False,
    'file_url': 'https://img.it-solution.ru/media/file_storage/000/000/000/008/WZUgws4E9bYhZtaAMO0-6ss7wtg.png',
    'file_name': 'ruwiki.png'
}

---------------------------------------------------------------------------------------------------

Пример сохранения скриншота GrabzIt в хранилище:

from its_utils.app_file_storage.functions.url_to_image import url_to_image

response = url_to_image(
    'https://it-solution.ru/',
    delay=30,
    file_name_without_ext='website',
    options={'browserHeight': -1}
)

ФОРМАТ УСПЕШНОГО РЕЗУЛЬТАТА url_to_image()
{
    'success': True,
    'url': 'https://fs.it-solution.ru/gf/?id=29&key=FQBYsak1Gj_NSV9wb7F-ZWZ4SdE',
    'error': ''
}

---------------------------------------------------------------------------------------------------

Пример сохранения файла по API методом POST при помощи api_key пользователя
# при этом сохранится владелец файла

import requests

RASCHLIST_KEY = 'ВАШ API KEY ПОЛЬЗОВАТЕЛЯ'
# можно найти ключ тут https://fs.it-solution.ru/admin/file_storage/usersettings/

file_from_internet_response = requests.get('https://ru.wikipedia.org/static/images/project-logos/ruwiki.png')

file_name = 'ruwiki.png'
file_content = file_from_internet_response.content

data = {
    'api_key': RASCHLIST_KEY
}

response = requests.post(
    "https://fs.it-solution.ru/add_file/",
    data=data,
    files={'file_for_storage': (file_name, file_content)}
).json()

ФОРМАТ УСПЕШНОГО РЕЗУЛЬТАТА add_file()
{
    'error': False,
    'file_id': 8,
    'file_datetime_created': '2021-08-09T19:50:59.283734+00:00',
    'url': 'ссылка на ваш файл'
}