import requests, webbrowser, os

def test_yaru():
    # Качнули главную страницу
    r = requests.get('https://ya.ru')

    # Сохранили как хтмл
    with open('c:/1/temptest.html', 'w') as f:
        f.write(r.text)

    # Сохранили как текст
    with open('c:/1/temptest.txt', 'w') as f:
        f.write(r.text)

    #открываем в браузере и исходный код
    webbrowser.open('c:/1/temptest.html')
    webbrowser.open('c:/1/temptest.txt')

    #или
    os.startfile('c:/1/temptest.html')
    os.startfile('c:/1/temptest.txt')



