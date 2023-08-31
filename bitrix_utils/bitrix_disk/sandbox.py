import requests
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.fields.files import FieldFile


def get_last_file_info():
    from bitrix_utils.bitrix_disk.models.bitrix_file import BitrixFile
    bitrix_file = BitrixFile.objects.filter(portal_id=3165).last()
    token = bitrix_file.portal.random_token(['itsolutionru.kdb'])
    file_info = bitrix_file.bx_rest_get(token)
    print(file_info)
    """{'ID': '534372', 'NAME': 'kdb_20230505.zip', 'CODE': None, 'STORAGE_ID': '2204', 'TYPE': 'file', 'PARENT_ID': '497452', 'DELETED_TYPE': '0', 'GLOBAL_CONTENT_VERSION': '1', 'FILE_ID': '959221', 'SIZE': '16076354', 'CREATE_TIME': '2023-05-06T00:45:12+03:00', 'UPDATE_TIME': '2023-05-06T00:45:12+03:00', 'DELETE_TIME': None, 'CREATED_BY': '1', 'UPDATED_BY': '1', 'DELETED_BY': '0', 'DOWNLOAD_URL': 'https://b24.it-solution.ru/rest/download.json?auth=a39f56640007783f500e7cd2e8cb3ee471d38c29382c&token=disk%7CaWQ9NTM0MzcyJl89ZzJqS1BCU1lSdmlhYkh2RGE4NDk3M0E5QjFBNXFhOXI%3D%7CImRvd25sb2FkfGRpc2t8YVdROU5UTTBNemN5Smw4OVp6SnFTMUJDVTFsU2RtbGhZa2gyUkdFNE5EazNNMEU1UWpGQk5YRmhPWEk9fGEzOWY1NjY0MDAwMDAxMzMwMDI0NDNjMDAwMDAwMDA4MDAwMDA3NzgzZjUwMGU3Y2QyZThjYjNlZTQ3MWQzOGMyOTM4MmMi.7hmInwKbNsIWYhIa2bFFBsAUDeye1tkHmabxXWwFRao%3D', 'DETAIL_URL': None}"""

    url = file_info['DOWNLOAD_URL']

    response = requests.get(url, timeout=300)

    # bitrix_file.file = File(response.content, file_info['NAME'])
    #bitrix_file.file = SimpleUploadedFile(file_info['NAME'], response.content, content_type="application/vnd.ms-excel")
    bitrix_file.file = SimpleUploadedFile(file_info['NAME'], response.content)
    bitrix_file.save()

    # with requests.get(url, stream=True, timeout=300) as file_resp:
    #     if not file_resp.ok:
    #         raise RuntimeError('status {}'.format(file_resp.status_code))
    #
    #     own_filename = '{f.portal_id}.{f.file_id}.{f.file_extension}'.format(f=disk_upload.bitrix_file)
    #     filename = os.path.join(catalog, own_filename)
    #     # Загружаем контент файла с битрикс-диска
    #     with open(filename, 'wb') as file_output:
    #         for chunk in file_resp.iter_content(256 * 1024):
    #             file_output.write(chunk)