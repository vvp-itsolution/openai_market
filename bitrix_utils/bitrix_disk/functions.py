import six

from bitrix_utils.bitrix_auth.models import BitrixUserToken
from bitrix_utils.bitrix_auth.models.bitrix_user_token import BitrixApiError
from bitrix_utils.bitrix_disk.exceptions import B24DiskRestError
from integration_utils.bitrix24.functions.call_list_method import CallListException

if six.PY2:
    Optional = None
else:
    from typing import Optional


def call_method(token,  # type: BitrixUserToken
                method,  # type: str
                params=None,  # type: Optional[dict]
                log_prefix='disk__',  # type: str
                list_method=False,  # type: bool
                **kwargs):
    if list_method:
        try:
            response = token.call_list_method_v2(
                method, params, log_prefix=log_prefix, **kwargs)
        except CallListException as e:
            six.raise_from(B24DiskRestError(
                method=method,
                response=e.args[0] if e.args else 'call_list_error',
            ), e)
        else:
            return response
    try:
        return token.call_api_method(
            method, params, log_prefix=log_prefix, **kwargs
        )['result']
    except BitrixApiError as e:
        six.raise_from(B24DiskRestError(
            method=method,
            response=e.json_response,
            code=e.status_code,
        ), e)


__all__ = 'call_method',
