


def list_to_matrix(items, indexes, indexes_settings={}):

    def fill_level(cursor, axis, indexes):
        for index in axis[indexes[0]]:
            #print("{} {}".format(indexes[0], index))
            if len(indexes) == 1:
                # Конечный уровень
                cursor.setdefault(index, None)
                pass
            else:
                cursor_to_pass = cursor.setdefault(index, dict())
                fill_level(cursor_to_pass, axis, indexes[1:])



    res = {}
    axis = {}
    for item in items:
        cursor = res
        for index in indexes:
            indexset = axis.setdefault(index, set())
            indexset.add(item[index])

            if index == indexes[-1]:
                cursor = cursor.setdefault(item[index], item)
            else:
                cursor = cursor.setdefault(item[index], dict())

    for index in indexes:
        axis[index] = axis[index] | set(indexes_settings.get(index, {}).get('add_indexes', ()))


    fill_level(res, axis, indexes)

    return res


class MatrixGenerator():
    def __init__(self, items):
        self.items = items

    def iter(self, key):
        for v in sorted(list(set([x[key] for x in self.items]))):
            yield v


if __name__ == '__main__':
    import os
    import sys

    import django

    FILE_PATH = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(os.path.join(FILE_PATH, '../../'))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    django.setup()

    from monitoring.models import ObserverRecordForMonth


    oo = [{'name': x['observer_line__name'], 'value': x, 'month': x['month'].month} for x in
          list(ObserverRecordForMonth.objects.filter(month__year=2020, observer_line__type_id=4).values(
              'month', 'id',
              'observer_line__name',
              'value'))]
    aa = MatrixGenerator(oo)
    print(list(aa.iter('name')))

    items = [{"a": 1, "b": 6}, {"a": 1, "b": 2}, {"a": 1, "b": 3}, {"a": 2, "b": 1}, {"a": 5, "b": 2},]



    #pprint(list_to_matrix(items, ['a', 'b'], indexes_settings={'b': {'add_indexes':[1,2,3,4,5,6,7,8,9,10]}}), indent=4, width=2)

    result = {
        1: {
            1: None,
            2: {"a": 1, "b": 2},
            3: {"a": 1, "b": 3},
            6: {"a": 1, "b": 5},
        },
        2: {
            1: {"a": 2, "b": 1},
            2: None,
            3: None,
            6: None,
        },
        5: {
            1: None,
            2: {"a": 5, "b": 2},
            3: None,
            6: None,
        },
    }
