import multiprocessing

def sleep():
    import time
    time.sleep(30)
    print('wakeupped')






if __name__ == '__main__':
    print('start')
    p = multiprocessing.Process(target=sleep, name="check_alerts", args=())
    p.start()