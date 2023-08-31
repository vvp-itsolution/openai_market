# -*- coding: utf-8 -*-
import base64
import datetime
import logging
import os.path
import random
import time

import requests
import six
from django.core.files.uploadedfile import SimpleUploadedFile
from six.moves.urllib.parse import urlencode
import unidecode

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.encoding import smart_text

from bitrix_utils.bitrix_auth.exceptions import BitrixApiError, ERROR_NOT_FOUND
from bitrix_utils.bitrix_auth.models import BitrixUserToken
from bitrix_utils.bitrix_disk.classes import Storage
from bitrix_utils.bitrix_disk.exceptions import B24DiskRestError
from bitrix_utils.bitrix_disk.functions import call_method
from integration_utils.bitrix24.functions.api_call import call_with_retries
from its_utils.app_admin.action_admin import ActionAdmin
from its_utils.app_secret.sign_string import get_string_secret
from settings import ilogger
from django.contrib import admin


def file_path(instance, filename):
    dirsecret = get_string_secret("{}_{}".format(instance.portal.id, instance.file_id))
    return "bitrixfields/portal_{}/{}-{}/{}".format(instance.portal.id, instance.file_id, dirsecret, filename)

@six.python_2_unicode_compatible
class BitrixFile(models.Model):
    # ID файла на B24 диске.
    # Уникален в рамках портала.
    file_id = models.IntegerField()
    filename = models.CharField(max_length=255)
    file_extension = models.CharField(max_length=255)
    portal = models.ForeignKey('bitrix_auth.BitrixPortal',
                               on_delete=models.PROTECT)
    uploaded_by = models.ForeignKey('bitrix_auth.BitrixUser', null=True,
                                    on_delete=models.SET_NULL, blank=True)
    # NB! Время создания записи о файле у нас,
    # сам файл на диске может быть старше.
    created = models.DateTimeField(default=timezone.now)
    last_check_access = models.DateTimeField(null=True, blank=True)

    file = models.FileField(null=True, blank=True, max_length=255, upload_to=file_path)

    class Admin(ActionAdmin):
        list_display = ['id', 'portal', 'file_id', 'filename', 'created', 'last_check_access']
        list_filter = ['portal']
        raw_id_fields = ['portal', 'uploaded_by',]
        actions = ['download_to_model', 'check_access', 'check_cache_file', 'upload_from_filefield']


    class Meta:
        unique_together = 'portal', 'file_id',

    def __str__(self):
        return u'#{self.id} domain: {self.portal.domain} ' \
               u'Disk ID: {self.file_id}'.format(self=self)

    def _update_fields_if_needed(self, bitrix_response):
        if self.pk is not None and bitrix_response['NAME'] != self.filename:
            self.filename = bitrix_response['NAME']
            self.save()
        return bitrix_response

    def save(self, *args, **kwargs):
        _, self.filename = os.path.split(smart_text(self.filename))
        _, ext = os.path.splitext(self.filename)
        self.file_extension = ext.lstrip('.')
        return super(BitrixFile, self).save(*args, **kwargs)

    def bx_rest_get(self, bitrix_user_token):
        # BitrixUserToken -> {'ID': ..., ...}
        return self._update_fields_if_needed(call_method(
            bitrix_user_token, 'disk.file.get', dict(id=self.file_id)
        ))

    def bx_rest_move_to_bin(self, bitrix_user_token):
        # BitrixUserToken -> {'ID': ..., ...}
        return self._update_fields_if_needed(call_method(
            bitrix_user_token, 'disk.file.markdeleted', dict(id=self.file_id)
        ))

    def bx_rest_delete(self, bitrix_user_token):
        # BitrixUserToken -> True
        return call_method(
            bitrix_user_token, 'disk.file.delete', dict(id=self.file_id)
        )

    @property
    def bitrix_url(self):
        """Прямая ссылка на файл, который можно скачать,
        имея куки-авторизацию на портале.
        """
        return 'https://{domain}/disk/downloadFile/{file_id}/?{q}'.format(
            domain=self.portal.domain,
            file_id=self.file_id,
            q=urlencode(dict(
                ncc='1',
                ts='bxviewer',
                filename=self.filename,
            ))
        )

    def dict(self):
        return dict(
            local_id=self.id,
            bitrix_id=self.file_id,
            filename=self.filename,
            file_extension=self.file_extension,
            portal_id=self.portal_id,
            portal_domain=self.portal.domain,
            uploaded_by_id=self.uploaded_by_id,
            created=self.created,
            bitrix_url=self.bitrix_url,
        )

    @classmethod
    def create_from_response(cls, file_response, **kwargs):
        bitrix_file = cls(file_id=int(file_response['ID']), **kwargs)
        bitrix_file._file_response = file_response
        return bitrix_file

    @staticmethod
    def encode_file_for_bitrix(file_, filename=None):
        """Описывается тут:
        https://dev.1c-bitrix.ru/rest_help/js_library/rest/files.php
        :param file_: `django.core.files.File`
        :param filename: str
        :return: list: [filename, b64 encoded str]
        """
        if filename is None:
            _, filename = os.path.split(file_.name)
        file_content = file_.file.read()
        b64_encoded = base64.b64encode(file_content)
        return [smart_text(filename), b64_encoded]

    def download_to_model(self, token=None):
        # Скачивает файл из Битрикс.Диска
        # кеширует(сохраняет в экземплляре модели) в FileField под названием file
        try:
            if not token:
                token = self.portal.random_token([settings.BITRIX_APP_CODE])
        except BitrixUserToken.DoesNotExist:
            return False

        try:
            file_info = token.call_api_method('disk.file.get', dict(id=self.file_id))['result']
        except BitrixApiError as e:
            if e.error == ERROR_NOT_FOUND:
                return False
            ilogger.warning('disk_file_get', "Нет информации о файле")
            raise e

        response = requests.get(file_info['DOWNLOAD_URL'], timeout=300)
        if response.status_code == 200:
            try:
                from its_utils.app_rfc6266 import pyrfc6266
                download_name = pyrfc6266.requests_response_to_filename(response)
                if download_name != file_info['NAME']:
                    ilogger.warn('rfc_name', 'didnt match ')
                    raise
            except:
                ilogger.error('rfc_name', 'error')
                raise
            self.filename = file_info['NAME']
            self.file = SimpleUploadedFile(file_info['NAME'], response.content)
            self.save()
        elif response.status_code == 503 and response.json().get('error') == 'QUERY_LIMIT_EXCEEDED':
            # TODO отдача файлов тоже может дать лимит, надо ли вынести в либу?
            time.sleep(random.randint(1, 5))
            return self.download_to_model()
        else:
            ilogger.error("file_download_not200", "err")
            raise

    def check_local_file_cache(self):
        # Если еще не загружали файл или удалили физически с диска
        if bool(self.file) == False or self.file.storage.exists(self.file.name)==False:
            #Кешируем с Битрикс диска
            self.download_to_model()

    def check_cache_file(self):
        # Проверить что кешированный файл совпадает с диском
        # сервисный метод для проверки порталов в ручную
        # приминение в проекте не ожидается
        token = self.portal.random_token([settings.BITRIX_APP_CODE])
        if not self.file:
            # Закешированного файла нет
            return True, 'Закешированного файла нет'

        file_info = token.call_api_method('disk.file.get', dict(id=self.file_id))['result']
        if int(file_info['SIZE']) != self.file.size:
            return False, f"{file_info['SIZE']=} {self.file.size=}"
        return  True, ''
        file_name = file_info['NAME'].replace(" — ", "__").replace('(', "").replace(")", "").replace(" ", "_").replace(",", "").replace(" — ", "__")
        if file_name == self.file.name.split("/")[-1]:
            # Если с заменненными символами совпадает
            #"ИП 1904_Вентиляционная решетка.pdf" -> "ИП_1904_Вентиляционная_решетка.pdf"
            return True, ''
        file_name, file_extention = os.path.splitext(file_name)
        if self.file.name.split("/")[-1].startswith(f"{file_name}_") and self.file.name.split(".")[-1].endswith(file_extention):
            # Если еще дописан рандом в конце
            # "ИП 1904_Вентиляционная решетка.pdf" -> "ИП_1904_Вентиляционная_решетка_gN4kmOH.pdf.pdf"
            return True, ''
        return False, f"{file_info['NAME']=} {self.file.name.split('/')[-1]=}"


    def check_access(self):
        # Проверяет доступность файла на Битрикс24 Диске

        try:
            token = self.portal.random_token([settings.BITRIX_APP_CODE])
            try:
                file_info = token.call_api_method('disk.file.get', dict(id=self.file_id))['result']
            except BitrixApiError as e:
                ilogger.warning('disk_file_get', "Нет информации о файле")
                return False
            self.last_check_access = timezone.now()
            self.save()
            return True
        except BitrixApiError:
            return False
        except B24DiskRestError:
            return False


    def upload_from_filefield(self, to_date_direcory=True):
        # Загружает файл в хранилище приложения
        # в папку сегодняшнего дня если to_date_direcory=True
        bitrix_user_token = self.portal.random_token(application_names=['itsolutionru.kdb'], is_admin=True)
        app_storage = Storage.get_app_storage(bitrix_user_token)
        if to_date_direcory:
            today_iso = datetime.date.today().isoformat()
            upload_folder, _ = app_storage.get_or_create_subfolder(
                bitrix_user_token,
                folder_name=today_iso,
            )
        else:
            upload_folder = None

        result = BitrixFile.bx_rest_upload(
            bitrix_user_token,
            storage=upload_folder,
            file_=self.file,
            instance=self

        )
        self.file_id=int(result['ID'])
        self.filename = result['NAME']
        self.save()

        return True







    @classmethod
    def bx_rest_upload(cls, bitrix_user_token, storage, file_,
                       filename=None, two_step=True,
                       tweak_non_unique_name=True, max_attempts=10, instance=None):
        """Загружает файл в хранилище или в папку.
        Чтобы изменить название загружаемого файла,
        надо изменить атрибут name у переданного файла.
        :param bitrix_user_token: `bitrix_auth.BitrixUserToken`
        :param storage: `bitrix_disk.classes.Storage`
        :param file_: `django.core.files.File`
        :param filename: optional string
        :param two_step: bool - Upload with multipart/form-data instead of b64;
        see https://dev.1c-bitrix.ru/rest_help/disk/folder/disk_folder_uploadfile.php
        :param tweak_non_unique_name: bool - При неуникальном имени файла,
        к названию будет добавлено ' (n)', где n - минимально необходимое
        число для уникального имени файла, начиная с 1.
        :param max_attempts: int - Сколько попыток непосредственно залить файл,
        актуально только при tweak_non_unique_name=True.
        Обычно достаточно лишь одной попытки, т.к. в большинстве случаев
        мы можем вычислить следующее имя файла, которое окажется уникальным.
        Необходимость повторных попыток вызвана заменой некоторых символов
        в именах файлов, т.к. полный список замены неизвестен.
        :rtype: BitrixFile
        :return: Загруженный на Битрикс-диск файл, + в атрибуте `_file_response`
        заманкипатчен ответ сервера о загрузке.
        """
        # Столько много всего, потому что:
        # 1) Существует 2 способа заливки файлов
        # 2) Мы пытаемся сохранить оригинальное название файла,
        # что довольно-таки большой геморрой
        def try_filenames(filename, limit=10):
            # NB! При двухшаговой загрузке битрикс
            # фейлится при передаче кириллических имен файлов,
            # При загрузке в 1 шаг такой проблемы нет.
            if two_step:
                filename = unidecode.unidecode_expect_ascii(filename)
            if not tweak_non_unique_name:
                # Передан параметр не пытаться установить уникальное имя файла
                yield filename
                return
            # Производим заранее известные замены как в Б24:
            # NB! список не полный и получен опытным путем!
            filename = filename.replace("'", '_')
            filename = filename.replace('&', '_')
            filename = filename.replace('~', '_')
            filename = filename.replace(';', '_')
            filename = filename.replace('#', '_')
            # todo: проверить символы: '!', '?', '*', '<', '>', '[', ']', '(', ')'

            head, ext = os.path.splitext(filename)
            head = head[:100]
            filename = head + ext
            # Сразу выбираем возможно совпадающие файлы и папки:
            # 1. Их имена содержат имя файла (без расширения)
            # 2. И они оканчиваются на то же расширение
            # (даже если это папка с именем 'foo.jpg')
            similar_neighbours = (
                neighbour['NAME'].lower() for neighbour in
                # {'%NAME': 'foo'} значит: WHERE UPPER(NAME) LIKE UPPER(%foo%)
                # другими словами, аналог джанговского:
                # .filter(NAME__icontains='foo')
                storage.get_children(bitrix_user_token, {'%NAME': head})
            )
            similar_neighbours = set(
                neighbour for neighbour in similar_neighbours
                if neighbour.endswith(ext.lower())
            )
            total_yields = 0
            if filename.lower() not in similar_neighbours:
                yield filename
                total_yields += 1
            n = 1
            while True:
                if total_yields >= limit:
                    return
                next_filename = u'{} ({}){}'.format(head, n, ext)
                if next_filename.lower() in similar_neighbours:
                    n += 1
                    continue
                else:
                    yield next_filename
                    total_yields += 1
                    n += 1

        # В параметрах первого запроса мы всегда передаем ID хранилища/папки.
        params = dict(id=storage.id)

        if two_step:
            # Загрузка в 2 шага, 1 запрос.
            if filename is None:
                _, filename = os.path.split(file_.name)
            filename = smart_text(filename)
            # Запрос для получения адреса заливки файла.
            result = call_method(
                bitrix_user_token, storage.upload_method, params
            )
            # Возвращен URL для multipart/form-data POST запроса
            upload_url = result['uploadUrl']
            b64_encoded = None
        else:
            # Загрузка в 1 шаг, подготавливаем данные.
            # Формируем пару [название, файл в b64].
            upload_url = None
            result = None
            filename, b64_encoded = cls.encode_file_for_bitrix(file_, filename)
        last_nonuniqe_filename_exc = None
        for filename in try_filenames(filename, max_attempts):
            if not two_step:
                # Заливка в 1 шаг файла в base64
                params['fileContent'] = [filename, b64_encoded]
                params['data'] = dict(NAME=filename)
                try:
                    result = call_method(
                        bitrix_user_token, storage.upload_method, params
                    )
                except B24DiskRestError as e:
                    if e.is_nonunique_filename_exc and tweak_non_unique_name:
                        # Файл с таким именем уже существует
                        # NB! В данной ветке мы вероятно встретились с неучтенной
                        # заменой символов на стороне Битрикса.
                        # Посылаем логгером ворнинг, чтобы добавить такую замену.
                        ilogger.warn(u'bad_upload_filename=> {}'.format(filename))
                        last_nonuniqe_filename_exc = e
                        continue
                    raise
                # Успешная заливка в один шаг b64encoded файла
                if instance == None:
                    return cls.create_from_response(
                        result,
                        portal=bitrix_user_token.user.portal,
                        uploaded_by=bitrix_user_token.user,
                        filename=result['NAME'],
                    )
                else:
                    return result

            # Заливка в 2 шага
            # Передаем в данных в параметре из первого запроса наш файл
            file_.file.seek(0)
            files = {result['field']: (filename, file_.file)}
            response = call_with_retries(upload_url, converted_params=None, files=files)

            response_data = response.json()
            if 'result' in response_data:
                if instance == None:
                    return cls.create_from_response(
                        response_data['result'],
                        portal=bitrix_user_token.user.portal,
                        uploaded_by=bitrix_user_token.user,
                        filename=response_data['result']['NAME'],
                    )
                else:
                    return response_data['result']
            # json не содержит поле 'result', вероятно ошибка от API B24
            exc = B24DiskRestError(upload_url, response=response_data,
                                   code=response.status_code)
            if exc.is_nonunique_filename_exc:
                # Неуникальное, имя файла, пробуем следующее
                # NB! В данной ветке мы вероятно встретились с неучтенной
                # заменой символов на стороне Битрикса.
                # Посылаем логгером ворнинг, чтобы добавить такую замену.
                ilogger.warn(u'bad_upload_filename=> {}'.format(filename))
                last_nonuniqe_filename_exc = exc
                continue
            raise exc
        else:
            # Исчерпано макс. кол-во попыток, кидаем последнюю ошибку о
            # неуникальном имени файла
            raise last_nonuniqe_filename_exc
