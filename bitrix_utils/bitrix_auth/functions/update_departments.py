# -*- coding: utf-8 -*-

from bitrix_utils.bitrix_auth.models import BitrixDepartment


def update_departments(portal, departments):

    """
    Для данного портала обновить список отделов.
    portal - объект BitrixPortal
    departments - список отделов в том виде, как его возвращает метод битрикса department.get
    Возвращает список отделов.
    """

    departments_map = {}

    existed_departments = {b.id: b for b in BitrixDepartment.objects.filter(portal=portal)}

    result = []
    for d in departments:
        department, _ = BitrixDepartment.objects.get_or_create(portal=portal, bitrix_id=d['ID'])
        department.name = d['NAME']

        parent = departments_map.get(d.get('PARENT'))
        if parent:
            department.parent = parent

        departments_map[d['ID']] = department
        department.save()

        # После того как уберем все только что обновленные отделы из этого словаря,
        # в нем останутся только отделы, удаленные на портале.
        try:
            del existed_departments[department.id]
        except KeyError:
            pass
        result.append(department)

    for d in existed_departments.values():
        d.delete()

    return result
