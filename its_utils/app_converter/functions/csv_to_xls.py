# -*- coding: UTF-8 -*-

import csv
import xlwt


# https://docs.python.org/2/library/csv.html#examples
def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, python=2, **kwargs):
    if python == 2:
        # csv.py doesn't do Unicode; encode temporarily as UTF-8:
        csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                                dialect=dialect, **kwargs)
        for row in csv_reader:
            # decode UTF-8 back to Unicode, cell by cell:
            yield [unicode(cell, 'utf-8') for cell in row]
    else:
        csv_reader = csv.reader(unicode_csv_data,
                                dialect=dialect, **kwargs)
        for row in csv_reader:
            yield [cell for cell in row]


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')


def csv_to_xls(csv_string, delimiter=',', python=2):

    """
    :param csv_string: CSV строка
    :param delimiter: Разделитель
    :param python: Версия питона (2 или выше)
    :return: xls файл
    """

    # http://techdetails.agwego.com/2006/10/24/30/
    csv_reader = unicode_csv_reader([row for row in csv_string.splitlines()], python=python, delimiter=delimiter)
    xls = xlwt.Workbook()
    table = xls.add_sheet('New Sheet')
    for i, row in enumerate(csv_reader):
        for j, data in enumerate(row):
            table.write(i, j, data)

    return xls


if __name__ == '__main__':
    f = csv_to_xls('\n'.join(u'1,2,3,"ывыuff",5,2.2' for _ in range(100)))
    f.save('test.xls')
