# -*- coding: utf-8 -*-

from bitrix_utils.bitrix_auth.models import BitrixGroup


def update_groups(portal, groups):

    """
    Для данного портала обновить список отделов.
    portal - объект BitrixPortal
    groups - список групп в том виде, как его возвращает метод битрикса sonet_group.get
    Возвращает список созданных групп.
    """

    existed_groups = {b.id: b for b in BitrixGroup.objects.filter(portal=portal)}

    result = []
    for g in groups:
        group, _ = BitrixGroup.objects.get_or_create(portal=portal, bitrix_id=g['ID'])
        group.name = g['NAME']
        group.save()

        try:
            # После того как уберем все только что обновленные группы из этого словаря,
            # в нем останутся только группы, удаленные на портале.
            del existed_groups[group.id]
        except KeyError:
            pass

        result.append(group)

    for group in existed_groups.values():
        group.delete()

    return result
