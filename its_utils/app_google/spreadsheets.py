def update_in_google_sheets(url, title, data, fields, lookup_field):
    """
    Выгрузить данные объекта в строку таблицы

    :param url: ссылка на google-таблицу
    :param title: имя таблицы (заголовок листа)
    :param data: объект
    :param fields: поля для выгрузки
    :param lookup_field: поле, по которому определяется уникальность объекта
    """

    from its_utils.app_google.classes import GspreadExportObject

    return GspreadExportObject(
        url, title, data, fields, lookup_field
    ).export()


def get_hyperlink_formula(url, title):
    """
    Получить формулу ссылки
    """

    return '=HYPERLINK("{url}"; "{title}")'.format(url=url, title=title)
