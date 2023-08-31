# -*- coding: utf-8 -*-
import six

from django.http import JsonResponse


@six.python_2_unicode_compatible
class B24DiskRestError(Exception):
    def __init__(self, method, response, code=None):
        self.method = method
        self.response = response
        self.code = code
        super(B24DiskRestError, self).__init__(method, response, code)

    def __str__(self):
        return '[{self.method}:{self.code}]\n{self.response!r}'.format(
            self=self,
            cls=self.__class__.__name__,
        )

    def dict(self):
        error = self.response if isinstance(self.response, dict) else dict(
            error=self.response,
        )
        error['_method'] = self.method
        error['_code'] = self.code
        return error

    def _get_http_status(self):
        if isinstance(self.code, six.integer_types):
            status = self.code
        elif isinstance(self.code, six.string_types) and self.code.isdigit():
            status = int(self.code)
        else:
            return 500
        if 100 <= status <= 599:
            return status
        return 500

    def json_response(self):
        error_dict = self.dict()
        status = self._get_http_status()
        json_error_response = JsonResponse(error_dict, status=status)
        if status >= 500:
            # skip django reports for 5xx responses
            json_error_response._has_been_logged = True
        return json_error_response

    @property
    def is_nonunique_filename_exc(self):
        # Такая ошибка возникает при неуникальном имени файла
        # или папки (sic!).
        return bool(
            self.response and isinstance(self.response, dict) and
            self.response.get('error') == 'DISK_OBJ_22000'
        )

    @property
    def is_upload_file_exc(self):
        # Такая ошибка возникает при загрузке файла, если кончается место,
        # возможно и в каких-то других случаях.
        return bool(
            self.response and isinstance(self.response, dict) and
            self.response.get('error') == 'DISK_FOLDER_22002'
        )
