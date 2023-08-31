/*
 Виджет выбора пользовтелей, групп и подразделений.
 Для активации надо подключить js файл и добавить SelectUsersWidget в зависимости основного приложения
 var app = angular.module('app', ['SelectUsersWidget']);
 И в шаблоне поставить
 <select-widget selected="{}" show-widget="showWidget" on-select="setAccess('save', selected)">
 <button>Изменить доступ</button>
 </select-widget>

 Внутри может быть любой html
 show-widget - булево значение. Показывать виджет или нет. Удобно, если надо прятать виджет не только по нажатию на кнопку
 selected - объект типа {0: [], 1: [], 2: [], 3: []} для объектов, которые уже были выбраны
 Причем директива понимает что 0 - это пользователи, 1 - группы, 2 - отделы и 3 - системные группы и т.д.
 Если добавятся новые типы не забывайте обновлять директиву.
 on-select - функция, которая будет вызвана после выбора объектов
 */
!function() {
    'use strict';
    var app = angular.module('SelectUsersWidget', []);

    app.filter('filterObject', function () {
        return function (items, filterValue) {
            if (!filterValue) {
                return items;
            }

            var filtered = [];
            filterValue = new RegExp(filterValue, 'gi');

            angular.forEach(items, function (item) {
                if ((item.FULL_NAME && item.FULL_NAME.search(filterValue) !== -1) ||
                    (item.NAME && item.NAME.search(filterValue) !== -1)) {

                    filtered.push(item);
                }
            });

            // angular.forEach(items, function (item) {
            //     if (item.NAME.search(filterValue) !== -1) {
            //         filtered.push(item);
            //     } else if (item.LAST_NAME && item.LAST_NAME.search(filterValue) !== -1) {
            //         filtered.push(item);
            //     }
            // });
            return filtered;
        }
    });

    app.directive('selectWidget', ['$parse', function ($parse) {

        return {
            restrict: 'E',
            templateUrl: '/static/bitrix_utils/select_widget/widget.html',
            transclude: true,
            scope: {
                showWidget: '=',
                selected: '=',
                onSelect: '&'
            },
            link: function (scope, element, attrs) {

                scope.users = [];
                scope.departments = [];
                scope.groups = [];
                scope.userFilter = '';
                scope.departmentFilter = '';
                scope.groupFilter = '';
                scope.allSelected = false;
                scope.errors = {};

                var keys = ['users', 'groups', 'departments'];

                var selectItems = function () {
                    // Заполнить пользователей, группы и отделы и отметить нужные
                    for (var j = 0; j < keys.length; j++) {
                        for (var i = 0; i < scope[keys[j]].length; i++) {
                            if (scope.selected[j] && scope.selected[j].indexOf(parseInt(scope[keys[j]][i].ID)) !== -1) {
                                scope[keys[j]][i].selected = true;
                            }
                        }
                    }
                    if (scope.selected[3]) {
                        scope.allSelected = (scope.selected[3].indexOf(0) !== -1);
                    }
                };

                scope.toggleObject = function (object) {
                    if (scope.allSelected) {
                        return;
                    }
                    object.selected = !object.selected;
                    //objectList[index].selected = !objectList[index].selected;
                };

                scope.closeWidget = function (event) {
                    if (event.target.id !== 'select-users-widget-wrapper') {
                        return;
                    }
                    scope.showWidget = false;
                };

                scope.toggle = function () {
                    scope.showWidget = !scope.showWidget;

                    if (!scope.showWidget) {
                        return;
                    }

                    delete scope.userFilter;
                    delete scope.departmentFilter;
                    delete scope.groupFilter;
                    scope.allSelected = false;

                    if (!(scope.users.length && scope.departments.length && scope.groups.length)) {

                        BX24.callMethod('user.get', {"ACTIVE": true}, function (response) {
                            var users = response.data();

                            users.forEach(function (element) {
                                if (element.NAME || element.LAST_NAME) {
                                    element['FULL_NAME'] = element.LAST_NAME + ' ' + element.NAME;
                                } else {
                                    element['FULL_NAME'] = element.EMAIL;
                                }
                            });

                            scope.users = scope.users.concat(users).sort(function (a, b) {
                                var A = a.FULL_NAME.toLowerCase();
                                var B = b.FULL_NAME.toLowerCase();

                                if (A < B)
                                    return -1;
                                if (A > B)
                                    return 1;
                                return 0;
                            });

                            if (response.more())
                                response.next();

                            selectItems();
                            scope.$apply();
                        });

                        BX24.callMethod('sonet_group.get', {}, function (response) {
                            var groups = response.data();

                            scope.groups = scope.groups.concat(groups);

                            if (response.more())
                                response.next();

                            selectItems();
                            scope.$apply();
                        });

                        BX24.callMethod('department.get', {}, function (response) {
                            var departments = response.data();

                            scope.departments = scope.departments.concat(departments);

                            if (response.more())
                                response.next();

                            selectItems();
                            scope.$apply();
                        });

                        // BX24.callBatch({
                        //     // users: ['user.get', {"ACTIVE": true}],
                        //     groups: ['sonet_group.get'],
                        //     departments: ['department.get', {}]
                        // }, function (response) {
                        //     for (var i = 0; i < keys.length; i++) {
                        //         scope[keys[i]] = response[keys[i]].data();
                        //         scope.errors[keys[i]] = response[keys[i]].error();
                        //     }
                        //     selectItems();
                        //     // В модели тип 3 - это системные группы, а если у такого типа значение 0 - это значит, что выбраны все пользователи
                        //     scope.$apply();
                        // });
                    } else {
                        // Асинхронность тудысюды
                        selectItems();
                    }
                };

                scope.selectAll = function () {
                    scope.allSelected = !scope.allSelected;
                };

                var getSelectedObjects = function () {
                    var selected = {};

                    if (scope.allSelected) {
                        // Пока так.
                        selected[3] = [0];
                    } else {
                        for (var i = 0; i < keys.length; i++) {
                            selected[i] = [];
                            for (var j = 0; j < scope[keys[i]].length; j++) {
                                if (scope[keys[i]][j].selected) {
                                    selected[i].push(parseInt(scope[keys[i]][j].ID));
                                    scope[keys[i]][j].selected = false;
                                }
                            }
                        }
                    }

                    return selected;
                };

                scope.select = function () {

                    scope.onSelect({selected: getSelectedObjects()});
                    scope.showWidget = false;
                };
            }
        };
    }]);

}();
