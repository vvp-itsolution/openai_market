var success = function(data) {
    console.log(data);
};

var error = function() {
    console.log('Error');
};

var uploadPhoto = function() {
    console.log('YOLOLOLOLO');
};

var submitArticle = function() {

    if (document.getElementById('title').value) {
        document.getElementById('article_form').submit();
    }
};

var resetContent = function() {
    console.log(window.articleBody);
    document.getElementById('article').value = window.articleBody;
};

var uploadOnChange = function() {
    angular.element(document.body).scope().upload();
};


var addImageToArticle = function(textarea, url) {

    var mdUrl = '\n![Описание изображения](' + url + ')\n',
        sStart = textarea.selectionStart,
        sEnd = textarea.selectionEnd,
        text = textarea.value,

        // textInside = text.substring(sStart, sEnd),
        textBefore = text.substring(0, sStart),
        textAfter = text.substring(sEnd, text.length);

    var newValue = textBefore + mdUrl + textAfter;
    textarea.value = newValue;

    sEnd += mdUrl.length;
    textarea.setSelectionRange(sEnd, sEnd);
    textarea.focus();
};

var insertToTextarea = function(textarea, value) {
    console.log(textarea, value);
    var sStart = textarea.selectionStart,
        sEnd = textarea.selectionEnd,
        text = textarea.value,

        textInside = text.substring(sStart, sEnd),
        textBefore = text.substring(0, sStart),
        textAfter = text.substring(sEnd, text.length);

    textarea.value = textBefore + value + textAfter;

    sStart += value[0].length;
    sEnd = sStart + textInside.length;
    textarea.setSelectionRange(sStart, sEnd);
    textarea.focus();
};

app = angular.module('app', []);


app.filter("sanitize", ['$sce', function($sce) {
    return function(htmlCode) {
        return $sce.trustAsHtml(htmlCode);
    }
}]);


app.controller('UploadImage', function($scope, $http) {
    window.s = $scope;

    $scope.directories = window.directories || [];
    $scope.currentDir = window.currentDir || "";
    $scope.images = window.images || [];
    $scope.rendered_body = '';
    $scope.articles = [];

    var successUpload = function(data) {
        $scope.images.unshift({
            pk: data.pk,
            url: data.url
        });
    };

    $http.get('/its/docs/api/v1/article.get_list/').then(function(response) {
                $scope.articles.data = response.data;
            }, function(error) {
                console.log(error);
            });
    var getArticlePk = function() {
        return angular.element('#article_pk')[0].value;
    };

    $scope.upload = function() {

        var data = new FormData();

        var article_pk = getArticlePk();
        var image = angular.element('#image_file')[0].files[0];

        data.append(article_pk, image);

        var settings = {
            transformRequest: window.angular.identity,
            headers: {
                'Content-Type': void 0
            }
        };

        $http.post('/its/docs/image_process/', data, settings).success(successUpload).error(error);
    };

    $scope.deleteImage = function(index, image_id) {
        $http.delete('/its/docs/image_process/?pk=' + image_id)
            .success(function() {
                $scope.images.splice(index, 1);
            }).error(error);
    };

    $scope.addImageToArticle = function(url) {
        addImageToArticle(angular.element('#article')[0], url);
    };

    $scope.getRender = function() {
        var data = {
            body: angular.element('#article')[0].value
        };

        $http.post('/its/docs/get_article_render/', data).success(function(data) {
            $scope.rendered_body = data;
        }).error(error);
    };

    $scope.deleteArticle = function(pk) {
        $http.delete('/its/docs/article_edit/' + pk + '/').success(function(data) {
            window.location = '/its/docs/';
        });
    };

    $scope.addUrlToArticle = function(pk, title) {
        var url = '[' + title +'](' + '/its/docs/article/' + pk + '/' + ')';
        insertToTextarea($('#article')[0], url);
    };

    $scope.changeDir = function(dirPk) {
        var data = {
            articlePk: getArticlePk(),
            dirPk : dirPk
        };

        $http.post('/its/docs/change_article_dir/', data).success(function(data) {
            $scope.currentDir = data;
        }).error(error);
    }

});
