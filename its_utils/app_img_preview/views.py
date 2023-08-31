# coding=utf-8
from __future__ import unicode_literals
import hashlib
import os

from django.conf import settings
from django.http import HttpResponseBadRequest, Http404, HttpResponseRedirect, HttpResponseNotFound
from settings import ilogger

from its_utils.app_get_params import get_params_from_sources

URL_IMG_DIR = 'app_img_perview/url_images/'

BLANK_IMAGE_RESOURCE_PATH = 'its_utils/app_img_preview/resources/blank_image.png'
BLANK_IMAGE_MEDIA_DIR = 'app_img_perview'
BLANK_IMAGE_NAME = 'blank_image.png'


def get_blank_image_path():
    media_root = settings.MEDIA_ROOT.rstrip('/')

    path = os.path.join(media_root, BLANK_IMAGE_MEDIA_DIR)
    if not os.path.exists(path):
        os.makedirs(path)

    if not os.path.isfile('{}/{}'.format(path, BLANK_IMAGE_NAME)):
        import shutil

        base_dir = settings.BASE_DIR.rstrip('/')
        src_path = os.path.join(base_dir, BLANK_IMAGE_RESOURCE_PATH)
        shutil.copy(src_path, path)

    return '{}/{}'.format(BLANK_IMAGE_MEDIA_DIR, BLANK_IMAGE_NAME)


@get_params_from_sources
def view_img_preview(request):
    """
        Создает превьюшку для изображения.
        :param request:
        :return: возвращает url изображения
    """

    # Достаем параметры из запроса
    image_path = request.its_params.get('image', 0)
    if image_path == "":
        image_path = get_blank_image_path()

    size = request.its_params.get('size', '100x100')
    crop = request.its_params.get('crop', 'center')
    new = request.its_params.get('new', 0)
    if crop == u'0':
        crop = None

    quality = int(request.its_params.get('quality', 100))
    format = request.its_params.get('format', "JPEG")

    media_root = settings.MEDIA_ROOT.rstrip('/')

    image_url = request.its_params.get('url')

    if image_url:
        enccoded_image_url = image_url.encode('utf-8')
        # Если был передан параметр url, сначала сохраняем картинку

        dir_path = os.path.join(media_root, URL_IMG_DIR)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        image_path = "{}{}.jpg".format(URL_IMG_DIR, hashlib.md5(enccoded_image_url).hexdigest())
        full_image_path = os.path.join(media_root, image_path)
        if new or not os.path.exists(full_image_path):
            # Если не передан параметр new, использум ранее скачанное изображение
            with open(full_image_path, 'wb') as handle:
                import requests
                response = requests.get(image_url)
                handle.write(response.content)

        image_path = "media/" + image_path

    # Если путь до изображения определен
    # Собираем абсолютный путь
    if image_path:
        image_path = image_path.lstrip('/')
        media_root = settings.MEDIA_ROOT.rstrip('/')
        # если путь не начинается с media и http://
        if image_path[:6] != 'media':
            image_path = image_path.split('media/', 1)[-1].lstrip('/')

        path = u"{}".format(os.path.join(media_root, image_path))

    else:
        return HttpResponseBadRequest('Provide path to image (?image=/media/path/to/im.jpg)')
        # Вернуть пустую картинку
        # path = os.path.join(settings.MEDIA_ROOT, 'blank_image.png')
    # Если по указанный путь ведет не к файлу

    if not os.path.isfile(path):
        # Кидаем ошибку
        ilogger.warn('img_preview_404','img_preview_404 {}'.format(path))
        return HttpResponseNotFound('not found {}'.format(image_path))

    if new:
        from sorl.thumbnail import delete as delete_thumbnail
        delete_thumbnail(path, delete_file=False)

    from sorl.thumbnail import get_thumbnail
    # Открываем файл
    img_file = open(path, 'rb')
    # Создаем превьюшку
    im = get_thumbnail(img_file, size, crop=crop, quality=quality, format=format)

    if request.its_params.get('rnd', 0):
        import random
        suffix='?%s' % random.randint(0, 1000000000000)
    else:
        suffix=''

    # Возвращаем url
    return HttpResponseRedirect("%s%s" % (im.url, suffix))
