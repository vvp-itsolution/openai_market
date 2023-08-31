#!!!!!!!!!!!!!! ПОКА ТОЛЬКО ЗАГОТОВКА!
# Первое использование в bitrix_events
from django.db import models
from django.utils import timezone

from its_utils.app_admin.get_admin_url import get_admin_a_tag
from settings import ilogger


class Locked(Exception):
    pass


class LockedTooLong(Exception):
    pass


class AbsLockerModel:

    # Модель мы для чего-то залочиваем, например для сбора евентов, для обработки событий, для еще чего-то поэтому
    # могут использоваться много различных полей для лока
    # для Лока мы будем использовать models.DateTimeField

    # КАК БЫЛО
    '''
            здесь lock_dt_for_collect_events является лог дейттамй полем

            НАЧАЛО!! ЗДЕСЬ ЛОЧИМ ОБЪЕКТ
            if InstanceClass.objects.filter(pk=self.pk, lock_dt_for_collect_events=None).update(lock_dt_for_collect_events=start_time) == 0:
                #Не удалось захватить объект для обработки
                # Функция берет всего 50 элементов, и логично что должна выполняться довольно быстро
                if (start_time-InstanceClass.objects.get(pk=self.pk).lock_dt_for_collect_events).seconds > 120:
                    raise CollectEventsLockedTooLong()
                raise CollectEventsLocked()

            ЗДЕСЬ ОБРАОБТКА!!!!

            КОНЕЦ!! РАЗЛАЧИВАЕМ ОБЪХЕКТ
            ЕСЛИ СЛУЧИТСЯ ОШИБКА, ТО ЗАЛОЧИТСЯ НАВСЕГДА
            if InstanceClass.objects.filter(pk=self.pk, lock_dt_for_collect_events=start_time).update(
                lock_dt_for_collect_events=None,
                force_collect_events=force_collect_events,
                last_collect_events=start_time) == 0:
                # не получилось по человечески снять лок
                ilogger.error('process_bitrix_events', 'Лок снят плохо!')

    '''

    # ЗАДАЧА СДЕЛАТЬ УДОБНЫЙ КЛАСС (ИНТЕРФЕЙС) +


    class LockOne:
        """
        Используя поле DateTime типа логически! лочит для определенного дейсвтвия модель

        Ожидается что типовое исопльзование расширяя модель джанги
        class AbsPortalEventSetting(models.Model, AbsLockerModel):

        Использование
        Вариант 1

        class AbsPortalEventSetting(models.Model, AbsLockerModel):
            ...
            ...
            def process(self):
                with self.lock_with_field('НазваниеПоляТипаDateTime'):
                    Что-то сделать

            или написать шорткаты под разную логику лока
            def lock_for_collect_events(self):
                return self.lock_with_field('имя поля для лока сбора евентов')

            и тогда
            def process(self):
                with self.lock_for_collect_events():
                    Что-то сделать

        """

        def __init__(self, obj, lock_field, too_long=120, unlock=False, unlock_after=None):
            self.obj = obj
            self.lock_field = lock_field
            self.too_long=too_long
            self.start_time = timezone.now()
            self.unlock = unlock

            # Разлачиваем после unlock_after секунд, или too_long умножить на 5
            # Если передан 0? то не будем разлачивать?
            if unlock_after == None:
                self.unlock_after = too_long * 5
            # FIXME!! если за пределами объект сохраняем, то дата лока обнуляется, тогда в __exit__ плохо.
            # поставил такую заглушку
            #self.__setattr__(lock_field, self.start_time)
            #МоОЖНО ИЗМЕЖАТЬ ИСПОЛЬЗУЮ DEFFER на это поле
            #!!!!!!!!chunk = OfflineBxEvent.objects.filter(status=OfflineBxEvent.NEW).defer('process_lock_dt')[:n]


        def __enter__(self):
            InstanceClass = self.obj.__class__
            if InstanceClass.objects.filter(pk=self.obj.pk, **{self.lock_field: None}).update(**{self.lock_field: self.start_time}) == 0:
                lock_time = InstanceClass.objects.get(pk=self.obj.pk).__getattribute__(self.lock_field)
                #Бывает что уже конкурентый процесс успел разлочить запись, поэтому lock_time может быть = None
                if lock_time and (self.start_time - lock_time).total_seconds() > self.too_long:
                    ilogger.warning('locked_too_long', '{} \nlock_time:{} \nnow:{}\ndelta={}'.format(
                        get_admin_a_tag(self.obj), lock_time, self.start_time, (self.start_time - lock_time).total_seconds()))
                    if self.unlock:
                        ilogger.error('deprecated_unlocked_too_long', 'fwefwefewf')
                        InstanceClass.objects.filter(pk=self.obj.pk).update(**{self.lock_field: None})
                        return None
                    if self.unlock_after > 0 and (self.start_time - lock_time).total_seconds() > self.unlock_after:
                        # Такая ситуация должна считаться нештатной, хорошо бы сюда не заходило. Но подчищает мусор без участия человека
                        InstanceClass.objects.filter(pk=self.obj.pk, **{self.lock_field: lock_time}).update(**{self.lock_field: self.start_time})
                        ilogger.error('unlocked_too_long', '{} \nlock_time:{} \nnow:{}\ndelta={}'.format(get_admin_a_tag(self.obj), lock_time, self.start_time, (self.start_time - lock_time).total_seconds()))
                        return None
                    raise LockedTooLong()
                raise Locked()
            return None

        def __exit__(self, type, value, traceback):
            InstanceClass = self.obj.__class__
            #print(InstanceClass.objects.filter(pk=self.obj.pk)[0].process_lock_dt)
            # когда мы залочивали модель на этом поле, то при выходе ожидаем что в lock_field до сих пор указано то время, которое было усановлео этим экземпляром контекст менеджера
            # бывают ситуации что пока модель была залочена, время в поле lock_field кто то изменил
            # 1) это может быть другой процесс
            # 2) ИЛИ когда производтися операция save над этим объектом СМ. комментарий выше в __init__
            if InstanceClass.objects.filter(pk=self.obj.pk, **{self.lock_field: self.start_time})\
                    .update(**{self.lock_field:None}) == 0:
                # не получилось по человечески снять лок
                lock_time = InstanceClass.objects.get(pk=self.obj.pk).__getattribute__(self.lock_field)
                ilogger.error('locker_model_bad_lock', 'Лок не снят или снят другим процессом!\n '
                                                       'Ожидалось время лока {}, а в БД {}\n'
                                                       'defer поля obj {}\n'
                                                       '{} Почитайте комментарии в коде рядом. может помочь использование deffer '
                              .format(self.start_time, lock_time, self.obj.get_deferred_fields(), get_admin_a_tag(self.obj)))
            return None

    def lock_with_field(self, lock_field, too_long=120, unlock=False):
        return self.LockOne(self, lock_field, too_long=too_long, unlock=unlock)

