from django.conf import settings
from django.core.signing import Signer


def get_string_secret(string, sign_key=None):
    # Принимает строку и секрет
    # возвращает строку которая уникальна для пары этих параметров
    # Например, может использоваться для раскладывания файлов в папке media
    # id файкл 33333 и мы бы положили в /media/files/33333333/file.txt
    # в этом случае злоумышленику надо знать имя файла и перебором поискать
    # с помощью этой функции надо сделать путь /media/files/33333333-KJFKJEewjfweuhfuewhfuwhwhef43823737fewf/file.txt
    # тогда не найти переобором этот файл
    # функция создана ради комментария и обучения, и шаблончика

    sign_key = sign_key or settings.SECRET_KEY
    signer = Signer(key=sign_key)
    # response = 3165_534393:WuDl5kHr4qS3whtXbj4KqUiryaI
    response = signer.sign(string)
    response = response.split(":")[1]

    return response
