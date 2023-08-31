import requests
import settings

from its_utils.app_file_storage.functions.sign_key import sign_key


def get_file(file_id, file_datetime_created):
    string_to_sign = '{}_{}'.format(file_id, file_datetime_created)
    key = sign_key(string_to_sign)
    data = {
        'key': key,
        'file_id': file_id,
        'file_datetime_created': file_datetime_created
    }
    response = requests.get(
        "https://" + settings.FILE_STORAGE_DOMAIN + "/get_file/",
        json=data
    )
    return response