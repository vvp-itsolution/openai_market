# -*- coding: utf-8 -*-
import enum
import six

from bitrix_utils.bitrix_disk.exceptions import B24DiskRestError
from bitrix_utils.bitrix_disk.functions import call_method


class FileType(str, enum.Enum):
    FILE = 'file'
    FOLDER = 'folder'


class StorageType(str, enum.Enum):
    STORAGE = 'storage'
    FOLDER = 'folder'

    @property
    def get_method(self):
        return {
            StorageType.STORAGE: 'disk.storage.get',
            StorageType.FOLDER: 'disk.folder.get',
        }[self]

    @property
    def upload_method(self):
        return {
            StorageType.STORAGE: 'disk.storage.uploadfile',
            StorageType.FOLDER: 'disk.folder.uploadfile',
        }[self]

    @property
    def add_folder_method(self):
        return {
            StorageType.STORAGE: 'disk.storage.addfolder',
            StorageType.FOLDER: 'disk.folder.addsubfolder',
        }[self]

    @property
    def get_children_method(self):
        return {
            StorageType.STORAGE: 'disk.storage.getchildren',
            StorageType.FOLDER: 'disk.folder.getchildren',
        }[self]

    @property
    def id_letter(self):
        return {
            StorageType.STORAGE: 's',
            StorageType.FOLDER: 'd',
        }[self]


@six.python_2_unicode_compatible
class Storage(object):
    def __init__(self, storage_type, storage_or_folder_id, get_response=None):
        self.storage_type = StorageType(storage_type)
        self.id = int(storage_or_folder_id)
        self.get_response = get_response

    def __str__(self):
        if self.get_response is not None:
            return u'<{}: #{} "{}">'.format(self.storage_type.name, self.id,
                                            self.get_response['NAME'])
        return u'<{}: #{} not loaded>'.format(self.storage_type.name, self.id)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return isinstance(other, Storage) and \
               other.storage_type == self.storage_type and other.id == self.id

    def __hash__(self):
        return hash((self.storage_type, self.id))

    @property
    def get_method(self):
        return self.storage_type.get_method

    @property
    def upload_method(self):
        return self.storage_type.upload_method

    @property
    def add_folder_method(self):
        return self.storage_type.add_folder_method

    @property
    def get_children_method(self):
        return self.storage_type.get_children_method

    @property
    def local_id(self):
        # Используется в OTDL, хранилища имеют строковой ID вида
        # 's-42', а папки вида 'd-42'
        return '{letter}-{id}'.format(
            letter=self.storage_type.id_letter,
            id=self.id,
        )

    @classmethod
    def get_app_storage(cls, bitrix_user_token):
        # Хранилище приложения, как посмотреть:
        # Диск -> Очистка местка -> Экспертный режим -> Повторить сканирование
        res = call_method(bitrix_user_token, 'disk.storage.getforapp')
        return cls(StorageType.STORAGE, res['ID'], res)

    @classmethod
    def get_storages(cls, bitrix_user_token, filter=None):
        # Возвращает все/отфильтрованные хранилища
        # NB! Битрикс может возвращать дублирующиеся записи.
        params = dict(filter=filter) if filter is not None else None
        return [
            cls(StorageType.STORAGE, storage['ID'], storage)
            for storage in call_method(
                bitrix_user_token,
                'disk.storage.getlist',
                params,
                list_method=True
            )
        ]

    @classmethod
    def get_group_storage(cls, bitrix_user_token, group_id):
        # Возвращает хранилище для раб. группы Б24 или None
        maybe_storage = call_method(bitrix_user_token, 'disk.storage.getlist', {
            'filter[ENTITY_TYPE]': 'group',
            'filter[ENTITY_ID]': group_id,
        })
        if maybe_storage:
            storage = maybe_storage[0]
            return cls(StorageType.STORAGE, storage['ID'], storage)

    def get(self, bitrix_user_token):
        # Возвращает информацию о хранилище
        res = call_method(bitrix_user_token, self.get_method, dict(id=self.id))
        self.get_response = res
        return res

    def get_children(self, bitrix_user_token, filter=None):
        # Возвращает все папки и файлы в данном хранилище/папке
        # NB! не рекурсивный метод, возвращает потомков только 1 уровня
        params = dict(id=self.id)
        if filter:
            params['filter'] = filter
        return call_method(bitrix_user_token, self.get_children_method,
                           params, list_method=True)

    def get_subfolders(self, bitrix_user_token, filter=None):
        # Возвращает все подпапки в данном хранилище/папке
        # NB! не рекурсивный метод, возвращает потомков только 1 уровня
        if filter is None:
            filter = {}
        else:
            assert 'TYPE' not in filter
        return [
            Storage(StorageType.FOLDER, folder['ID'], folder)
            for folder in self.get_children(
                bitrix_user_token, dict(TYPE=FileType.FOLDER.value, **filter)
            )
        ]

    def get_files(self, bitrix_user_token, **filter):
        # Возвращает все файлы в данном хранилище/папке
        # NB! не рекурсивный метод, возвращает потомков только 1 уровня
        if filter is None:
            filter = {}
        assert 'TYPE' not in filter
        return self.get_children(bitrix_user_token, dict(
            TYPE=FileType.FILE.value,
            **filter
        ))

    def add_subfolder(self, bitrix_user_token, folder_name, data=None):
        # Добавляет дочернюю папку в данное хранилище/папку
        if data is None:
            data = {}
        assert 'NAME' not in data
        data['NAME'] = folder_name
        params = dict(id=self.id, data=data)
        res = call_method(bitrix_user_token, self.add_folder_method, params)
        return Storage(StorageType.FOLDER, res['ID'], res)

    def get_or_create_subfolder(self, bitrix_user_token, folder_name,
                                default_folder_data=None):
        # Возвращает подпапку из данного хранилища/папки с заданным названием,
        # иначе создает дочернюю папку с таким названием
        folders = self.get_subfolders(bitrix_user_token, dict(NAME=folder_name))
        if folders:
            # Такая папка уже есть, возвращаем
            return folders[0], False
        try:
            # Папки нет создаем
            return self.add_subfolder(bitrix_user_token, folder_name,
                                      data=default_folder_data), True
        except B24DiskRestError as e:
            if e.is_nonunique_filename_exc:
                # Вероятнее всего папка была создана конкурирующим запросом
                # такое может встречаться при одновременной заливке
                # нескольких файлов разными запросами.
                folders = self.get_subfolders(bitrix_user_token,
                                              dict(NAME=folder_name))
                if folders:
                    return folders[0], False
            raise
