window.api_url = '/its/model_view/api';

var app = angular.module('modelViewApp', ['agGrid', 'ui.bootstrap', 'treeControl']);

app.controller('MainCtrl', function ($scope, $http, $window) {
    window.s = $scope;
    $scope.foreignKey = 'ForeignKey';
    $scope.app = window.appName;
    $scope.model = window.modelName;

    $scope.gridOptions = {
        enableColResize: true,
        showToolPanel: true,
        enableSorting: true,
        onReady: function () {
            $scope.gridOptions.api.sizeColumnsToFit()
        }
    };

    $scope.data = [];
    $http.get(window.api_url + '/get_model_fields/', {
        params: {
            a: $scope.app,
            m: $scope.model
        }
    }).then(function (response) {
        $scope.data = response.data;
        for (var i = 0; i < $scope.data.fields.length; i++) {
            $scope.data.fields[i].model = $scope.data.model;
            $scope.data.fields[i].app = $scope.data.app;

            if ($scope.data.fields[i].type !== $scope.foreignKey) {
                $scope.selectedNodes.push($scope.data.fields[i]);
            }
        }
    });

    $scope.getFieldsForForeign = function(node) {
        if (!node.children) {
            $http.get(window.api_url + '/get_model_fields_for_foreign/', {
                params: {
                    a: node.app,
                    m: node.model,
                    f: node.label
                }
            }).then(function(response){
                for (var i = 0; i < response.data.fields.length; i++) {
                    response.data.fields[i].model = response.data.model;
                    response.data.fields[i].app = response.data.app;
                    response.data.fields[i].parent = node;
                }
                node.children = response.data.fields;
            });
        }
    };

    $scope.treeOptions = {
        dirSelectable: false,
        multiSelection: true,
        isLeaf: function(node) {
            return node.type !== $scope.foreignKey;
        },
        injectClasses: {
            iLeaf: '',
            iExpanded: '',
            iCollapsed: '',
        }
    };

    var prepareTable = function (fields) {

        var columns = [];

        for (var i = 0; i < fields.length; i++) {
            columns.push({
                field: fields[i],
                headerName: fields[i]
            });
        }

        $scope.gridOptions.api.setColumnDefs(columns)
    };

    $scope.unselectAll = function() {
        $scope.selectedNodes = [];
        $scope.selectAll = true;
    };

    var selectAllChildren = function(node) {
        if (node.children) {
            for (var i = 0; i < node.children.length; i++) {
                    selectAllChildren(node.children[i]);
                }
            } else if (node.type !== $scope.foreignKey) {
                $scope.selectedNodes.push(node);
            }

    };

    $scope.selectAllNodes = function(node) {
        $scope.selectedNodes = [];
        for (var i = 0; i < $scope.data.fields.length; i++) {
            selectAllChildren($scope.data.fields[i]);
        }
        $scope.selectAll = false;
    };

    $scope.getData = function() {
        var node,
            field = '',
            fields = [];

        for (var i = 0; i < $scope.selectedNodes.length; i++) {
            node = $scope.selectedNodes[i];
            field = '';
            while (node.parent) {
                field = node.label + '__' + field;
                node = node.parent;
            }
            field = node.label + '__' + field;
            fields.push(field.substring(0, field.length - 2));
        }

        if (!fields.length) {
            return;
        } else {
            $scope.currentFields = fields;
        }

        prepareTable(fields);
        $http.get(window.api_url + '/get_model_data/', {
            params: {
                f: fields.join(','),
                a: $scope.app,
                m: $scope.model
            }
        }).then(function (response) {
            $scope.gridOptions.api.setRowData(response.data);
        });
    };

    $scope.export = function() {
        var params = '?a=' + $scope.app + '&m=' + $scope.model + '&f=' + $scope.currentFields.join(',');
        $window.open(window.api_url + '/export/' + params, '_blank');
    };

    $scope.clearTable = function() {
        $scope.gridOptions.api.setRowData([]);
    };
});
