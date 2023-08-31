app.directive('markdownPanel', ['$http', function($http) {

    var HEADER_ICON = 'glyphicon glyphicon-header';

    var TABLE_MARKDOWN = '\n-----------------------------| -----------------------------' + '\n' +
        'Содержимое ячейки  | Содержимое ячейки' + '\n' +
        'Содержимое ячейки  | Содержимое ячейки';


    var buttonList = [
        [{
            icon: 'glyphicon glyphicon-bold',
            textToInsert: ['**', 'жирный', '**']
        }, {
            icon: 'glyphicon glyphicon-italic',
            textToInsert: ['_', 'курсив', '_']
        }],
        [{
            icon: HEADER_ICON,
            textToInsert: ['#', 'Заголовок 1', '']
        }, {
            icon: HEADER_ICON,
            textToInsert: ['##', 'Заголовок 2', '']
        }, {
            icon: HEADER_ICON,
            textToInsert: ['###', 'Заголовок 3', '']
        }, {
            icon: HEADER_ICON,
            textToInsert: ['####', 'Заголовок 4', '']
        }, {
            icon: HEADER_ICON,
            textToInsert: ['#####', 'Заголовок 5', '']
        }, {
            icon: HEADER_ICON,
            textToInsert: ['######', 'Заголовок 6', '']
        }],
        [{
            icon: 'glyphicon glyphicon-picture',
            textToInsert: ['![Описание изображения](', 'Ссылка на изображение', ')']
        }, {
            icon: 'glyphicon glyphicon-link',
            textToInsert: ['[Описание ссылки](', 'Ссылка', ')']
        }],
        [{
            icon: 'glyphicon glyphicon-list',
            textToInsert: ['1. ', 'Элемент списка', '']
        }, {
            icon: 'glyphicon glyphicon-list-alt',
            textToInsert: ['* ', 'Элемент списка', '']
        }, {
            icon: 'glyphicon glyphicon-asterisk',
            textToInsert: ['`', 'Код', '`']
        }, {
            icon: 'glyphicon glyphicon-comment',
            textToInsert: ['>', 'Цитата', '']
        }],
        [{
            icon: 'glyphicon glyphicon-th',
            textToInsert: ['Заголовок 1                | ', 'Заголовок 2', TABLE_MARKDOWN]
        }, {
            icon: 'glyphicon glyphicon-chevron-down',
            textToInsert: ['!~~~Спойлер\n', 'Текст спойлера', '\n/~~~']
        }]
    ];

    var customButtonList = [
        [{
            icon: 'glyphicon glyphicon-plus',
            callback: function () {
                $('#myModal').modal('show');
            }
        }]
    ];

    var Button = function(panel, icon, textToInsert, callback) {
        this.button = document.createElement('div'); // if button some weird stuff going on with jquery. Screw it.
        var iElem = document.createElement('i');
        iElem.className = icon;

        if (icon == HEADER_ICON) {
            iElem.innerHTML = textToInsert[0].length;
        }

        this.button.className = 'btn btn-default btn-sm';

        this.button.appendChild(iElem);

        this.panel = panel;
        this.textToInsert = textToInsert;

        if (callback) {
            // Если есть какой-то свой callback, то вызывается он
            // В функцию передается этот объект.
            // Иначе - стандартная вставка символов.
            this.button.onclick = (function (button) {
                return function () {
                    callback(button)
                };
            })(this);
        } else {
            this.button.onclick = function (button) {
                return function () {
                    button.panel.insertToTextarea(button.textToInsert);
                };
            }(this);
        }

        return this.button;
    };

    var Panel = function(scope, textarea, buttonList, customButtonList) {

        this.addButton = function(div, icon, textToInsert, callback) {
            var button = new Button(this, icon, textToInsert, callback);
            div.appendChild(button);
            this.buttons.push(button);
        };

        this.addButtonsFromList = function(list) {
            var btnGroup;

            for (var i = 0; i < list.length; i++) {
                btnGroup = document.createElement('div');
                btnGroup.className = 'btn-group';
                for (var j = 0; j < list[i].length; j++) {
                    this.addButton(btnGroup, list[i][j].icon, list[i][j].textToInsert, list[i][j].callback);
                }

                this.panel.appendChild(btnGroup);
            }
        };

        this.insertToTextarea = function(value) {
            var sStart = this.textarea.selectionStart,
                sEnd = this.textarea.selectionEnd,
                text = this.textarea.value,

                textInside = text.substring(sStart, sEnd),
                textBefore = text.substring(0, sStart),
                textAfter = text.substring(sEnd, text.length);

            if (!textInside) {
                textInside = value[1];
            }

            this.textarea.value = textBefore + value[0] + textInside + value[2] + textAfter;

            sStart += value[0].length;
            sEnd = sStart + textInside.length;
            this.textarea.setSelectionRange(sStart, sEnd);
            this.textarea.focus();
        };

        this.scope = scope;
        this.panel = document.createElement('div');
        this.panel.id = 'ts-markdown-panel';
        this.panel.className = 'btn-toolbar';
        this.textarea = textarea;
        this.buttons = [];

        if (buttonList) {
            if (customButtonList) {
                buttonList = buttonList.concat(customButtonList);
            }

            this.addButtonsFromList(buttonList);
        }

        this.textarea.parentElement.insertBefore(this.panel, this.textarea);
    };


    var addPanels = function(scope, textarea) {
        new Panel(scope, textarea, buttonList, customButtonList);
    };

    return {
        link: function(scope, element) {
            addPanels(scope, element[0]);
        }
    }
}]);
