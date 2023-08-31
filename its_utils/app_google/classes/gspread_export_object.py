import json
import os

from oauth2client.service_account import ServiceAccountCredentials

import gspread

from gspread import WorksheetNotFound, Cell
from gspread import utils as gs_utils

from django.conf import settings


class GspreadExportObject:
    """
    Класс представляет данные объекта для выгрузки в строку google-таблицы
    """

    __GS_SCOPE = ('https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive')
    __SERVICE_KEY_PATH = os.path.join(settings.BASE_DIR, 'its_utils/app_google/credentials/g-service-key.json')

    __FLOAT_COMPARISON_PRECISION = 1e-8

    __JSON_FIELD = 'JSON'

    def __init__(self, url, title, data, fields, lookup_field):
        """
        :param url: ссылка на google-таблицу
        :param title: имя таблицы (заголовок листа)
        :param data: объект
        :param fields: поля для выгрузки
        :param lookup_field: поле, по которому определяется уникальность объекта
        """

        self.url = url
        self.title = title
        self.data = data
        self.lookup_field = lookup_field

        self.fields = [f for f in fields if f not in (self.lookup_field, self.__JSON_FIELD)]
        self.fields.insert(0, self.lookup_field)
        self.fields.insert(len(self.fields), self.__JSON_FIELD)

        self.spreadsheet = None
        self.worksheet = None

    def export(self):
        """
        Выгрузить данные объекта в строку таблицы
        """

        # список списков ячеек (минимум 1 строка - для заголовка)
        rows_list = self.get_spreadsheet_rows(1, len(self.fields))

        fields_index = dict()  # ключи этого словаря - поля, значения - номера колонок
        cells_list = []  # список обновлённых ячеек

        # Заголовки колонок
        # -----------------------
        header_row = rows_list[0]

        cur_col = 1  # индексы ячеек начинаются с 1 !!!

        for cell in header_row:
            # if not cell.value:
                # Заголовки закончились
                # break

            try:
                # Если заголовок найден в списке полей, запоминаем его индекс
                field = next(f for f in self.fields if self.__eq(f, cell.value))
                fields_index[field] = cur_col

            except StopIteration:
                # Если не найден, пропускаем
                continue

            finally:
                cur_col += 1

        # Добавление новых заголовков
        for field in [f for f in self.fields if f not in fields_index.keys()]:
            cells_list.append(Cell(1, cur_col, field))
            fields_index[field] = cur_col
            cur_col += 1
        # --------------

        # Строки данных
        # ---------------
        row_found = False
        cur_row = 2

        for row in rows_list[1:]:
            lookup_cell = row[fields_index[self.lookup_field] - 1]
            if not lookup_cell.value or self.__eq(lookup_cell.value, self.data[self.lookup_field]):
                # значение lookup_field в строке пустое или совпадает с объектом - нашли нужную строку

                row_found = True

                for index, field in self.__sort_by_value(fields_index):
                    cell = row[index - 1]
                    value = self.get_value(field)

                    if not self.__eq(cell.value, value):
                        cells_list.append(Cell(cur_row, index, value))

                break

            cur_row += 1

        if not row_found:
            # Не нашли строку - вставляем новую

            # Заполнить строку пустыми значениями
            # Могут быть колонки, для которых нет индекса. Например, если поле удалили
            values = [None] * max(fields_index.values())

            for f, i in fields_index.items():
                values[i - 1] = self.get_value(f)

            self.worksheet.insert_row(values, cur_row, value_input_option='USER_ENTERED')
        # -------------------------------------------------------------------------------

        # Обновить изменённые ячейки
        if cells_list:
            self.worksheet.update_cells(cells_list, value_input_option='USER_ENTERED')

        return len(cells_list)

    def open_spreadsheet(self):
        """
        Получить таблицу и рабочий лист
        """

        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.__SERVICE_KEY_PATH, self.__GS_SCOPE)
        self.spreadsheet = gspread.authorize(credentials).open_by_url(self.url)

        try:
            self.worksheet = self.spreadsheet.worksheet(self.title)

        except WorksheetNotFound:
            self.worksheet = self.spreadsheet.add_worksheet(self.title, 0, 0)

    def get_spreadsheet_rows(self, rows_count, cols_count):
        """
        Получить диапазон ячеек

        rows_count и cols_count - минимальное количество
        Если строк/колонок больше, будут получены все строки/колонки

        :return: список списков ячеек
        """

        if not self.worksheet:
            self.open_spreadsheet()

        cols_count = max(self.worksheet.col_count, cols_count)
        rows_count = max(self.worksheet.row_count, rows_count)

        rows_to_add = rows_count - self.worksheet.row_count
        if rows_to_add > 0:  # если на листе не хватает строк
            self.worksheet.add_rows(rows_to_add)

        cols_to_add = cols_count - self.worksheet.col_count
        if cols_to_add > 0:  # если на листе не хватает столбцов
            self.worksheet.add_cols(cols_to_add)

        # Получить список всех ячеек для заполнения
        cell_range = '{}:{}'.format(
            gs_utils.rowcol_to_a1(1, 1),
            gs_utils.rowcol_to_a1(rows_count, cols_count)
        )
        cell_list = self.worksheet.range(cell_range)

        return [cell_list[i:i + cols_count] for i in range(0, len(cell_list), cols_count)]

    def get_value(self, field):
        """
        Получить значение поля объекта
        """

        if field == self.__JSON_FIELD:
            value = self.data

        else:
            value = self.data.get(field)

        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)

        if value is None:
            value = ''

        return value

    @classmethod
    def __eq(cls, a, b):
        """
        Сравнить два значения

        При записи в таблицу могут меняться типы данных: записали float 0.42 - получили строку "0,42"
        """

        if isinstance(a, (float, int)) or isinstance(b, (float, int)):
            return cls.__compare_numeric(a, b)

        # todo: сравнение формул
        # Если записываем формулу, например =HYPERLINK("http://фффф.ru"; "link"), то значение ячейки, которое получим
        # от api в следующий раз, будет просто "link", поэтому все ссылки будут перезаписываться при каждом экспорте

        return a == b

    @classmethod
    def __compare_numeric(cls, a, b):
        """
        Сравинть два числа
        """

        try:
            if isinstance(a, str):
                a = float(a.replace(',', '.'))

            if isinstance(b, str):
                b = float(b.replace(',', '.'))

            return abs(a - b) < cls.__FLOAT_COMPARISON_PRECISION

        except ValueError:
            return False

    @staticmethod
    def __sort_by_value(d):
        """
        Необходимо, чтобы ячейки одной строки в списке, который передаётся в update_cells, следовали по возрастанию
        номера колонки. Этот метод принимает словарь, в котором ключ - поле объекта, значение - соответствующий номер
        колонки; сортирует по возрастанию номеров колонок.

        :param d: {<Поле>: <Номер ячейки>}
        :return: сортированный список кортежей (<Номер ячейки>, <Поле>)
        """

        return sorted((i, f) for (f, i) in d.items())
