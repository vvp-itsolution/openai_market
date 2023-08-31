# -*- coding: UTF-8 -*-

'''its/docs
##view_automaticly_fetch_docs.py

Модуль, генерирующий документацию на основе комментариев.

Для работы необходимы:
список репозиториев `ITS_UTILS_DOCUMENTATION['DOC_REPOSITORIES_TO_CLONE']`
и словарь с разрешениями файлов и регулярными выражениями
`ITS_UTILS_DOCUMENTATION['SUPPORTED_FILES_AND_REGEXP']`
its/docs'''

import os
import re
import shutil
import tempfile

from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.admin.views.decorators import staff_member_required
# from django.core.urlresolvers import reverse

from its_utils.functions.sys_call import sys_call

from its_utils.app_documentation.documentation_settings import ITS_UTILS_DOCUMENTATION
from its_utils.app_documentation.models import Article, Directory
from its_utils.its_settings import ITS_UTILS_PATH


TEMP_DIR = os.path.join(ITS_UTILS_PATH, ITS_UTILS_DOCUMENTATION['REPOS_TEMPDIR_NAME'])


def parse_text(text, regexp, code_bloc_regexp=None):
    out = []

    if code_bloc_regexp:
        regexp = '|'.join(regexp, code_bloc_regexp)

    for result in re.findall(regexp, text, re.DOTALL):
        block = []
        for line in result.splitlines():
            block.append(line.lstrip())

        out.append('\n'.join(block))

    return '\n\n'.join(out)


def get_github_url(repo_url, path, filename):
    '''its/docs
    ####Функция get_github_url

    #####Возвращает
    Ссылку на гитхаб. Пример:
    https://github.com/user/TestingDocs/blob/master/dir/test.js
    its/docs'''

    try:
        repo_url = re.search(r'github\.com.*', repo_url).group()
    except TypeError:
        return None

    return 'http://{}/blob/master{}/{}'.format(repo_url, path, filename)


def create_and_get_directory(name, path):
    '''its/docs
    ####Функция create_and_get_directory

    Конвертирует путь в объекты модели Directory.
    Возвращает последнюю директорию, к которой надо
    привязать статью.

    #####Параметры
    path - путь относительно временной папки (пример 'repo.git/static/dir')

    its/docs'''

    dirs = [name] + path.split(os.sep)
    parent = None

    for dirname in dirs:

        if not dirname:
            continue

        directory, _ = Directory.objects.get_or_create(parent=parent, name=dirname)
        parent = directory

    return directory


def get_parsed_data_from_dir(dirname):
    '''its/docs
    ####Функция get_parsed_data_from_dir
    #####Параметры
    dirname - полный путь к каталогу сколонированному (/home/.../tempfolder/repo.git/)
    #####Результат
    пример
    ```
    [
        ('', 'main_readme_file.md', 'Разметка маркдаун'),
        ('static', 'app.js', 'Разметка маркдаун'),
    ]
    ```
    its/docs'''

    data = []

    for directory, _, files in os.walk(dirname):
        for filename in files:
            ext = os.path.splitext(filename)[-1]

            if ext in ITS_UTILS_DOCUMENTATION['SUPPORTED_FILES_AND_REGEXP']:
                path = os.path.join(directory, filename)

                with open(path, 'rt') as text:
                    parsed_data = parse_text(
                        text.read(), ITS_UTILS_DOCUMENTATION['SUPPORTED_FILES_AND_REGEXP'][ext])
                    data.append((directory.replace(dirname, ''), filename, parsed_data))

    return data


def get_or_create_article(title, directory, data, user, github_url=''):
    '''its/docs
    ####Функция get_or_create_article
    #####Параметры
    * title - Строка. Имя статьи.
    * directory - Объект Directory. Директория, где лежит статья
    * data - Строка. Текст статьи
    * user - Объект User.
    #####Возвращает
    Кортеж:
    * Объект статьи
    * Булево значение (создана или нет)
    its/docs'''

    try:
        article = Article.objects.get(title=title,
                                      directory=directory,
                                      deleted=False)
    except ObjectDoesNotExist:
        article = Article(title=title, directory=directory)
        created = True
    else:
        created = False

    article.auto_fetched = True
    article.body = data
    article.user = user
    article.github_url = github_url
    article.save()

    return article, created


def get_key(data, created=None, diff=None):
    '''its/docs
    ####Функция get_key
    Возвращает ключ для словаря results в зависимости от действий со статьей.
    Статья может быть пропущена, создана, изменена и не изменена.
    its/docs'''

    if not data:
        return 'skipped'

    if created:
        return 'created'

    if diff:
        return 'edited'
    else:
        return 'unmodified'


def fetch_articles(request):
    '''its/docs
    ####Функция fetch_articles

    При вызове, по порядку клонирует репозитории,
    указанные в `ITS_UTILS_DOCUMENTATION['DOC_REPOSITORIES_TO_CLONE']`,
    Ищет все комментарии, относящиеся к документации и создает статью на их основе.

    Возвращает словарь с репозиториями и
    результатом работы (новые, измененные, неизмененные и нетронутые статьи)
    its/docs'''

    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    PKs = []
    repositories = ITS_UTILS_DOCUMENTATION['DOC_REPOSITORIES_TO_CLONE']

    results = {
        'repos': {},
        'deleted': [],
    }

    for url in repositories:
        repo_name = url.split('/')[-1]
        dirname = tempfile.mkdtemp(dir=TEMP_DIR)
        code, output = sys_call(
            'git clone {} -b {} {}'.format(url, 'master', dirname))

        if code != 0:
            error = output
        else:
            error = None

        results['repos'][repo_name] = {key: []
                                       for key
                                       in ('created', 'edited', 'deleted',
                                           'skipped', 'unmodified', 'error')}

        if error:
            results['repos'][repo_name]['error'] = [err for err in error.splitlines()]
            break

        for dirpath, filename, data in get_parsed_data_from_dir(dirname):
            if data:
                directory = create_and_get_directory(repo_name, dirpath)
                github_url = get_github_url(url, dirpath, filename)
                article, created = get_or_create_article(filename,
                                                         directory,
                                                         data,
                                                         request.user,
                                                         github_url)
                pk = article.pk
                key = get_key(data, created, article.diff)
                PKs.append(pk)
            else:
                pk = None
                key = get_key(data)

            results['repos'][repo_name][key].append((pk, filename))

    articles_to_delete = Article.objects.filter(auto_fetched=True,
                                                deleted=False).exclude(pk__in=PKs)
    results['deleted'] = list(articles_to_delete)
    articles_to_delete.update(deleted=True)

    return results


@staff_member_required
def view_auto_doc(request):
    '''its/docs
    ####Функция view_auto_doc

    Возвращает результат работы функции fetch_articles.
    its/docs'''

    results = fetch_articles(request)
    context = {
        'results': results,
        'deleted': results['deleted']
    }

    template = 'documentation/fetch_result.html'
    return render(request, template, context)
