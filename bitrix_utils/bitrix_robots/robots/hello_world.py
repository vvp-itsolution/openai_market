from django.http import HttpResponse

from bitrix_utils.bitrix_auth.models import BitrixUserToken

from ..base import RobotBase


class HelloWorldRobot(RobotBase):
    """Робот для примера, робот отправляет пост в живую ленту, использование:

    0. Нужен портал с деморежимом, развернутое приложение с правами:
        - bizproc (Бизнес-процессы, нужно всем роботам)
        - log (Живая лента, нужно этому конкретному роботу)
    1. в urls.py
    urlpatterns = [
        ...
        'robot/hello.world/', HelloWorldRobot.as_view(), name='robot_hello_world',
        ...
    ]
    2. при запуске приложения (допустим в главной view):
        if not HelloWorldRobot.is_installed(admin_token):
            HelloWorldRobot.install(
                view_name='robot_hello_world',  # name из url.py
                admin_token=request.bx_user_token.upgrade_to_admin(),
            )
    [Удаление] Удаление робота с портала:
        HelloWorldRobot.delete(admin_token)

    Как работает:
        - заходим в CRM на портале с включенными БП (деморежим)
        - у сделки/лида настраиваем роботов на вкладке роботы
        - добавляем робота - "Пост в живую ленту" на опр. стадию
        - при перетаскивании лида/сделки на эту стадию происходит пост
    """
    # Уникальный код робота
    CODE = 'ITS-ROBOT-HELLO-WORLD'
    # Название для интерфейса Б24
    NAME = 'Пост в живую ленту'
    # Входные параметры
    PROPERTIES = dict(
        title=dict(
            Name='Заголовок',
            Type='string',
            Required='Y',
        ),
        message=dict(
            Name='Сообщение',
            Type='text',
            Required='Y',
            Multiple='Y',
        )
    )
    # Опционально можно вернуть значение и оно будет доступно другим роботам
    RETURN_PROPERTIES = dict(
        postId=dict(
            Name='ID поста',
            Type='int',
            Required='Y',
        )
    )

    # Бизнес-логика робота описывается в методе process
    def process(self, token: BitrixUserToken, props: dict) -> HttpResponse:
        # 0. Если запрос доходит до этого места, то мы можем быть
        # уверены, что он не поддельный. Токен генерируется для пользователя,
        # чьим токеном производилась встройка. Параметры робота пока
        # просто собираются в словарь и никак не преобразовываются.

        # 1. С переданным токеном и props выполняем необходимые действия
        post_id = token.call_api_method('log.blogpost.add', dict(
            POST_TITLE=props['title'],
            POST_MESSAGE='\n'.join(props['message']),
        ))['result']
        # 2. Если есть возвращаемые параметры - ответ битриксу
        token.call_api_method('bizproc.event.send', dict(
            event_token=self.event_token,
            return_values=dict(postId=post_id),
        ))
        # 3. Отдаем ответ, чтобы робот отвис в Б24
        return HttpResponse('ok')
