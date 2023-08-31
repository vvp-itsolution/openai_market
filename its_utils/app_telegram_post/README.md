### Использование


~~~~
its_utils.app_telegram_post.post_to_telegram.post_to_telegram
post_to_telegram(chat_id, message)
~~~~


chat_id  = "-айди группы"  или  chat_id  = "@имягруппы"

Сообщение пишется от @tickets_its_bot
для того чтобы бот мог написать, надо его пригласить в группу

Как узнать -айди группы?

1) Создаем группу
2) Добавляем туда бота по имени @tickets_its_bot
3) Переводим в супергруппу
4) делаем ее публичной и задаем любое имя например qwdqwdqwodkoqwkdokqwd
5) переходим по ссылке подставив вместо qwdqwdqwodkoqwkdokqwd название своей группы
https://telegram-client.it-solution.ru/pub_message/?chat_id=@qwdqwdqwodkoqwkdokqwd&message=wefwfe123
6) в ответе приходит чат id: -10012423238676522,
7) делаем группу обратно закрытой
8) проверяем постинг по id https://telegram-client.it-solution.ru/pub_message/?chat_id=-10012423238676522&message=wefwfe123
9) теперь вы знаете id группы "10012423238676522"





