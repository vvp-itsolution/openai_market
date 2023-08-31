import time

class TimeIt:
    """
    Можно вычислить время выполенния кода в with

    with TimeIt() as ti:
        count = ps.collect_bitrix_events()
        print('wefwefwef)

    ti.start_time - время начала в микро или даже меньше секундах
    ti.start_time - время окончания в микро или даже меньше секундах
    ti.duration - время выполнения

    """

    def __init__(self):
        pass

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, type, value, traceback):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        return None


#def timeit()