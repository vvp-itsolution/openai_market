import requests
import settings

from its_utils.app_file_storage.functions.sign_key import sign_key


def add_file(file_name, file_content):
    string_to_sign = file_name
    key = sign_key(string_to_sign)
    data = {
        'key': key
    }
    response = requests.post(
        "https://" + settings.FILE_STORAGE_DOMAIN + "/add_file/",
        data=data,
        files={'file_for_storage': (file_name, file_content)}
    )
    return response