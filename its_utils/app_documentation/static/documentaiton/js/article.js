'use strict';

var menu = document.getElementsByTagName('menu')[0];
var article = document.getElementById('article');
var headers = article.querySelectorAll('h1, h2, h3, h4');

for (var i in headers) {

    if (!headers[i].innerHTML) {
        continue;
    }

    headers[i].id = headers[i].innerHTML;
    var a = document.createElement('a');
    a.href = '#' + headers[i].id;
    a.className = 'list-group-item hidden-overflow';
    var li = document.createElement('li');
    li.innerHTML = headers[i].innerHTML;

    a.appendChild(li);
    menu.appendChild(a);

    var span = document.createElement('span');
    span.className = 'edit glyphicon glyphicon-pencil';
    span.setAttribute('ng-click', 'editPart("' + headers[i].id +'")');
    headers[i].appendChild(span);
}


var app = angular.module('app', []);


app.controller('MainCtrl', function($scope, $http) {

    var getBodyPart = function(body, id) {

        var header = document.getElementById(id);
        var headerText = header.childNodes[0].innerHTML || header.childNodes[0].nodeValue;
        var headers = [];
        var hSize = parseInt(header.nodeName.slice(1));

        for (var i = hSize; i > 0; i--) {
            headers.push('h' + i);
        }

        headers = document.getElementById('article').querySelectorAll(headers);
        for (i = 0; i < headers.length; i++) {
            if (header == headers[i]) {
                i++;
                for (i; i < headers.length; i++) {
                    if (hSize >= parseInt(headers[i].nodeName.slice(1))) {
                        var nextHeader = headers[i].childNodes[0].innerHTML || headers[i].childNodes[0].nodeValue;
                        break;
                    }
                }
                break;
            }
        }

        var start,
            end;

        for (i = 0; i < body.length; i++) {
            if (body[i].search(headerText) !== -1) {
                start = i;
                if (nextHeader) {
                    i++;
                    for (i; i < body.length; i++) {
                        if (body[i].search(nextHeader) !== -1) {
                            end = i;
                            break;
                        }
                    }
                }
            }
        }

        if (!end) {
            end = i;
        }

        $scope.start = start;
        $scope.end = end;
        return body.slice(start, end).join('\n');
    };

    var editPart = function(body, id) {
        $scope.bodyPart = getBodyPart(body, id);
        $scope.editedBodyPart = angular.copy($scope.bodyPart);
        $('#articlePartialEdit').modal('show');
    };

    $scope.editPart = function(id) {

        if ($scope.body) {
            editPart($scope.body, id);
        } else {
            $http.get('/its/docs/api/v1/article.get_raw/', {params:{id: window.articleId}}).then(function(response) {
                $scope.body = response.data.split('\n');

                editPart($scope.body, id);

            });
        }
    };

    var saveArticle = function() {
        var newBody = $scope.body.slice(0, $scope.start).join('\n') + '\n' + $scope.editedBodyPart + '\n' +
            $scope.body.slice($scope.end, $scope.body.length).join('\n');

        console.log(newBody);
        $http.post('/its/docs/api/v1/article.save/', {id: window.articleId, body: newBody}).then(function() {
            delete $scope.body;
            delete $scope.bodyPart;
            delete $scope.editedBodyPart;
            location.reload();
        });
    };

    $scope.saveArticlePart = function() {
        if ($scope.bodyPart !== $scope.editedBodyPart) {
            saveArticle();
        }
        $('#articlePartialEdit').modal('hide');
    }
});
