# coding: utf-8

from django.conf import settings


'''its/docs
##Настройки документации.

Если в ссылке репозитория `'DOC_REPOSITORIES_TO_CLONE'` указать имя и пароль,
то необходимо указать порт git'a 9418, чтобы ссылка выглядела так:
`'https://user:password@github.com:9418/hlopikit/its_utils.git'`
its/docs'''


ITS_UTILS_DOCUMENTATION = {
    'MARKDOWN_EXTENSIONS': (
        # built-in
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.nl2br',
        # custom
        'its_utils.md_extentions.mdx_spoiler',
        'its_utils.md_extentions.mdx_urlize',
        'its_utils.md_extentions.mdx_mytables',
    ),

    'MAIN_ARTICLE': 'main',
    'MAIN_ARTICLE_TITLE': 'Документация',

    'REPOS_TEMPDIR_NAME': 'docs_temporary_clonned',
    # Кортеж ссылок на репозитории из которых будет собрана документация.
    'DOC_REPOSITORIES_TO_CLONE': (),
    # {расширение: (регулярное выражение для комментариев, регулярное выражение для блоков кода)}
    'SUPPORTED_FILES_AND_REGEXP': {
        '.js': r'''/\*its/docs(.+?)its/docs\*/''',
        '.py': r'''['"]{3}its/docs(.+?)its/docs['"]{3}''',
        '.md': r'''its/docs(.+)''',
    },
    'SAFE_MARKDOWN': 'escape',
}


ITS_UTILS_DOCUMENTATION.update(getattr(settings, 'ITS_UTILS_DOCUMENTATION', {}))
