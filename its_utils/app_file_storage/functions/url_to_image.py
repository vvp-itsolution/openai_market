import settings
import requests

def url_to_image(url, delay=0, file_name_without_ext='', options=None):
    api_key = settings.FILE_STORAGE_API_KEY

    data = {
        'url': url,
        'api_key': api_key,
        'delay': delay,
        'file_name_without_ext': file_name_without_ext,
        'options': options,
    }

    response = requests.post(
        "https://" + settings.FILE_STORAGE_DOMAIN + "/save_img_with_grabzit/",
        json=data
    )

    return response