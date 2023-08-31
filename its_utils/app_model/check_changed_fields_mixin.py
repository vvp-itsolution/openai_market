from django.db import models


class CheckChangedFieldsMixin:
    """
    Класс добавляет функцию контроля изменения полей
    """

    def changed_fields(self, fields):
        # Проверяет поля на изменение по списку
        # Принимает List ['id', 'portal_id']
        # Возвращает List измененных или пустой []

        from_db = self.__class__.objects.get(pk=self.pk)
        result = {'from_db_object': from_db, 'changed': []}
        for field in fields:
            if getattr(self, field) != getattr(from_db, field):
                result['changed'].append(field)

        return result

