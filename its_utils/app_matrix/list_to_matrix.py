import collections
from pprint import pprint, pformat

"""
Использование
Модель выручки по менеджерам по месяцам
def MonthAmount(models.Model):
    manager = ForeignKey(User)
    month = DateTime() # Предположим на начало месяца может быть 2020-01-01 или 2020-02-01
    amount = Integer
    
Нам надо вывести  django шаблон (есть regroup tag но он не заполянет пропущенные ячейки)
          
          Январь Февраль Март ... Деакбрь
Иванов     200    200     200       0                
Петров     200    100      0        0                
Сидоров    200    100      0        0             

Для этого нам нужна двойная итерация, но из БД мы получим только существующие записи + в виде одного вектора 

#Делаем запрос 
ma = MonthAmount.objects.filter(month__year=2020)

#Можно сразу с именами юзеров
ma = MonthAmount.objects.filter(month__year=2020).values('month__month', 'id', 'amount', 'manager__name')

#можно доп поля подготовить для красивых имен индексов
ma = [{**x, "name":x['manager__name'], "month":x.["month__month"]} for x in list(a)]

In Python 3.5 or greater:
z = {**x, **y} объединение ключей словарей

li = ListIndex(ma, ["name", "month"])

# Добавим чтобы в табилце учавствовали все месяца
li.axises['month'] = [1,2,3,4,5,6,7,8,9,10,11,12]

# Отсортировать индекс
li.axises['name'] = sorted(li.axises['name'])

#Получить готовую матрицу
oo = li.iterator.matrix()
[
    [None, 200, None, None, None, None, None, None, None, None, None, None],
    [None, 100, 100, 100, None, None, None, None, None, None, None, None],
    [100, 200, 100, 100, None, None, None, None, None, None, None, None],
    [None, 200, None, 100, None, None, None, None, None, None, None, None],
]


#Итерироваться можно как-то так.
res = []
    for a in aa.iter():
        res_b = []
        for b in a.iter():
            res_b.append(b)
        res.append(res_b)




"""
#TODO много здесь чего передалать
#1) именовать переменные по человечески
#2) смущают iterator и items() на одном уровене
#3) Сортировки
#4)

class AxisedList():
    # Лист разложенный по Осям например x,y,z,....

    def __init__(self, items, axises_names):
        self.items = items
        self.axises_names = axises_names
        index = {}
        axises = {}  # оси {'x':[1,2,3,4]}

        for position, item in enumerate(items):
            cursor = index
            for axis_name in axises_names:
                # Добавляем метку на ось
                axises.setdefault(axis_name, set()).add(item[axis_name])

                if axis_name == axises_names[-1]:
                    # Добавляем в словарь указатель на позицию в листе
                    cursor = cursor.setdefault(item[axis_name], position)
                else:
                    # Добавляем измерение/ось
                    cursor = cursor.setdefault(item[axis_name], dict())

        self.index = index
        self.axises = {key: list(value) for key, value in axises.items()}
        self.iterator = AxisedList.Iterator(self, axises_names[0])
        #self.iter = self.iterator.iter

    def get_by_index(self, position):
        index = self.index
        for pos in position:
            index = index.get(pos, None)
            if index == None:
                return None
        return self.items[index]

    class Iterator():

        def __init__(self, list_index, index, position=[]):
            self.index = index
            self.list_index = list_index
            self.level = list_index.axises_names.index(index)
            self.position = position

        def one_of(self):
            # Дать первый подходящий под вектор элемент
            # может нужно для красивого представления
            index = self.list_index.index
            for pos in self.position:
                index = index.get(pos, None)

            return self.list_index.items[index[next(iter(index))]]

        def matrix(self):
            # bb = aa.iterator.matrix()
            # возвращает матрицу из элементов list в list итд...
            # [
            #   [1,2,3],
            #   [5,2,3],
            #   [1,6,3],
            # ]
            res = []
            for i in self.iter():
                if isinstance(i, self.__class__):
                    res.append(i.matrix())
                else:
                    res.append(i)
            return res

        def iter(self):

            for pos in list(self.list_index.axises[self.index]):
                # Перебираем все отметки на оси
                position = self.position + [pos]
                if self.level != len(self.list_index.axises_names) - 1:
                    # не конечная выборка
                    yield self.__class__(self.list_index, self.list_index.axises_names[self.level+1], position)
                else:
                    yield self.list_index.get_by_index(position)



def test_on_lines():
    from monitoring.models import ObserverRecordForMonth

    oo = [{'name': x['observer_line__name'], 'value': x, 'month': x['month'].month} for x in
          list(ObserverRecordForMonth.objects.filter(month__year=2020, observer_line__type_id=4).values(
              'month', 'id',
              'observer_line__name',
              'value'))]
    aa = AxisedList(oo, ['name', 'month'])

    res = []
    for a in aa.iter():
        res_b = []
        for b in a.iter():
            res_b.append(b)
        res.append(res_b)

    # Теперь поменяем ось



    return aa, res

