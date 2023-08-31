Виждет для выбора пользователя/группы/подразделения для встраиваемых приложений Б24
===================================================================================

Использование без систем сборки:
--------------------------------
```html
<script src='/static/bitrix_auth/select_user/dist/bundle-[VERSION].js'>

<script>
!function() {
  var openSelector = window.bitrixSelector.openSelector;
  var closeSelector = window.bitrixSelector.closeSelector;
  
  myBtnElement.addEventListener('click', function() {
    openSelector({
      // 'user', 'sonet_group' or 'department'
      mode: 'user',
      // Сюда вернется выбранный пользователь или список, если задано multiple: true
      callback: function(user) { /* do your stuff */ },
      // Опицонально
      // Колбек при закрытии модалки (закрытие с выбором или без выбора)
      onClose: function() { },
      // Можно ли выбрать нескольких пользователь
      // По умолч. false
      multiple: false,
      // Разрешать ли пустой выбор? (в callback передается null или [])
      // По умолч. false
      allowEmpty: false,
      // Опционально
      // ID уже выбранного пользователя
      // или список таких ID (при multiple true)
      // или null
      initiallySelected: '5',
      // Опицонально
      // Способ отфильтровать пользователей.
      // По умолчанию отображаются все пользователи
      filter: function(user) { return user.ID !== '42'; },
      // Опционально: язык 'ru' или 'en'
      locale: 'ru',
      // Опционально: стили
      style: {
        top: '100px',
        'background-color': 'lightgrey',
      },
      // По умолчанию пользователи/группы/отделы
      // получаются вызовом BX24.callMethod(...)
      // Это можно изменить, воспользовавшись данным параметром:
      entities: [
        {ID: '15', NAME: 'Вася', ...},
      ],
      // Также можно передавать Promise типа Promise<Array<Object>, Error>
      // стоит обратить внимание на типы: resolve всегда длолжен отдавать
      // список объектов с полями как у user.get/department.get/sonet_group.get,
      // Для отображения собственного сообщения об ошибке
      // reject всегда должен бросать ошибку с полем message,
      // `throw new Error('error message')` подойдет.
      entities: axios.get('/api/get_my_users/')
        .then(function(resp) { return resp.data.users; })
        .catch(function(e) {
          const resp = e && e.resp;
          const data = resp && resp.data;
          const status = resp && resp.status;
          const errorMessage = data && data.error
            ? String(data.error)
            : (status ? 'Ошибка сервера' : 'Ошибка соединения');
          throw new Error(errorMessage);
        }),
      // Опицонально: исключить из списка пользователей глючных коробочных чатботов
      // По-умолчанию: false
      // NB! требует REST-права imbot
      // Работает с параметром entities или без, всегда полагается на window.BX24
      // https://ts.it-solution.ru/#/ticket/50807/
      excludeBoxChatbots: true,
    });
  }, false);
}();
</script>
```

Установка с npm
---------------

```bash
$ npm install --save-dev bitrix_utils/bitrix_auth/bitrix_selector
```
Или добавить в настройки webpack:
```bash
cd bitrix_utils/bitrix_auth/bitrix_selector && yarn install
```
```js
module.exports = {
    resolve: {
        extensions: [ '.js' ],
        modules: [
          path.join(__dirname, 'bitrix_utils/bitrix_auth'),
        ],
    },
};
```

Использование с ES модулями
---------------------------
```js
import { openSelector, closeSelector } from 'bitrix_selector';
// Далее аналогично
```
