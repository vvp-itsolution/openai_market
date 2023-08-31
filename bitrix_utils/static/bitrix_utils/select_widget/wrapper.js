// Обертка над angular-виджетом выбора прав пользователей
// для использования без ангуляра.
// Статика шаблона и стиль должны быть доступны по конкретному пути:
// - /static/bitrix_utils/select_widget/widget.html
// - /static/bitrix_utils/select_widget/widget.css
// Доп. статика:
// - Должен быть подключен bitrix_utils/css/bitrix.css
// - Если не подключить bootstrap@3 чуть едут стили,
//   попытался немного подправить
// - Должна быть подключена библиотека BX24
//   (см. также пропатченную версию BX24 в Базе Знаний)
// Без сборки:
// Подключаем widget.js и wrapper.js <script> тегами
// ```js
// window.selectWidgetWrapper.createApp({
//   showOnStart: false,
//   // DOM-element or selector for angular.element
//   // defaults to document.body
//   el: '#my-container',
//   html: '<button type="button">Права доступа</button>',
//   onSelect: ({ selected }) => doYourStuffWith(selected),
// });
// ```
// Со сборщиком (webpack):
// - Добавляем в resolve.modules вебпака path.join(__dirname, 'path/to/bitrix_utils/static')
// ```js
// import { createApp } from 'bitrix_utils/select_widget/wrapper';
// createApp({ ... });
// ```
// Требует подключенного/установленного ангуляра 1.5.8-1.7.5

(function(root, factory) {
  // UMD https://github.com/umdjs/umd/blob/master/templates/commonjsStrictGlobal.js
  if (typeof define === 'function' && define.amd) {
    // AMD. Register as an anonymous module.
    define(['exports', 'angular', './widget.js'], function(exports, angular) {
      factory((root.selectWidgetWrapper = exports), angular);
    });
  } else if (typeof exports === 'object' && typeof exports.nodeName !== 'string') {
    // CommonJS
    require('./widget.js');
    factory(exports, require('angular'));
  } else {
    // Browser globals
    factory((root.selectWidgetWrapper = {}), root.angular);
  }
}(typeof self !== 'undefined' ? self : this, function(exports, angular) {
  'use strict';
  var WIDGET_APP_NAME = 'SelectUsersWidget';
  var WIDGET_DIRECTIVE_NAME = 'select-widget';
  var __i = 0;
  var wrapperAppName = function() {
    return 'selectWidgetWrapperApp' + __i;
  }
  var controllerName = function() {
    return 'selectWidgetWrapperController' + __i;
  }

  function getAppElement(innerHtml) {
    var wrapperAppDiv = document.createElement('div');
    wrapperAppDiv.setAttribute('ng-controller', controllerName());
    var widgetAppDiv = document.createElement(WIDGET_DIRECTIVE_NAME);
    widgetAppDiv.setAttribute('selected', 'selected');
    widgetAppDiv.setAttribute('show-widget', 'showWidget');
    widgetAppDiv.setAttribute('on-select', 'onSelect(selected)');
    angular.element(widgetAppDiv).append(innerHtml);
    wrapperAppDiv.appendChild(widgetAppDiv);
    return wrapperAppDiv;
  }

  exports.createApp = function(options) {
    ++__i;
    var WRAPPER_APP_NAME = wrapperAppName();
    options = angular.extend({}, options);
    if (!options.hasOwnProperty('el')) {
      options.el = document.body;
    } else {
      options.el = angular.element(options.el)[0];
    }
    if (!options.hasOwnProperty('selected')) {
      options.selected = {};
    } else {
      options.selected = angular.copy(options.selected);
    }
    if (!options.hasOwnProperty('showOnStart')) {
      options.showOnStart = false;
    }
    if (!options.hasOwnProperty('onSelect')) {
      options.onSelect = angular.noop;
    }
    if (!options.hasOwnProperty('html')) {
      options.html =
        '<button type="button">Изменить доступ</button>';
    }
    var appElement = getAppElement(options.html);
    var ctrl = null;
    var $destroy = null;
    options.el.appendChild(appElement);
    var app = angular
      .module(WRAPPER_APP_NAME, [])
      .controller(controllerName(), [
        '$scope', '$rootScope', function($scope, $rootScope) {
          ctrl = $scope;
          $scope.selected = options.selected;
          $scope.showWidget = options.showOnStart;
          $scope.onSelect = options.onSelect;
          $destroy = $rootScope.$destroy.bind($rootScope);
        }
      ]);

    angular.element(function() {
      angular.bootstrap(appElement, [WRAPPER_APP_NAME, WIDGET_APP_NAME]);
    })
    return {
      app: app,
      destroy: function() {
        if (ctrl === null) {
          return console.error("couldn't destroy app, uninitialized?");
        }
        $destroy();
        options.el.removeChild(appElement);
      },
      updateModel: function(selected) {
        if (ctrl === null) { return console.error('uninitialized?'); }
        ctrl.selected = angular.copy(selected);
      },
      showWidget: function() {
        if (ctrl === null) { return console.error('uninitialized?'); }
        ctrl.showWidget = true;
        if (!ctrl.$$phase) { ctrl.$apply(); }
      },
      hideWidget: function() {
        if (ctrl === null) { return console.error('uninitialized?'); }
        ctrl.showWidget = false;
        if (!ctrl.$$phase) { ctrl.$apply(); }
      },
    };
  }
}));
