"""Битриксовый BBCODE -> html
(описание задач + сообщения в живой ленте)
"""
import os
import re

import bbcode
import django
from django.conf import settings
from django.utils.html import format_html


bb_parser = bbcode.Parser()


def _register_formatter(tag_name, **kwargs):
    def decorator(formatter):
        bb_parser.add_formatter(tag_name, formatter, **kwargs)
        return formatter
    return decorator

# Поддерживаемые по умолчанию теги:
# https://bbcode.readthedocs.io/en/latest/tags.html
# Теги, поддерживаемые в Б24
# https://helpdesk.bitrix24.ru/open/6060589/


bb_parser.add_simple_formatter('table', '<table>%(value)s</table>', strip=True,
                               swallow_trailing_newline=True,
                               transform_newlines=False, replace_links=False,
                               replace_cosmetic=False)
bb_parser.add_simple_formatter('thead', '<thead>%(value)s</thead>', strip=True,
                               swallow_trailing_newline=True,
                               transform_newlines=False, replace_links=False,
                               replace_cosmetic=False)
bb_parser.add_simple_formatter('tbody', '<tbody>%(value)s</tbody>', strip=True,
                               swallow_trailing_newline=True,
                               transform_newlines=False, replace_links=False,
                               replace_cosmetic=False)
bb_parser.add_simple_formatter('tfoot', '<tfoot>%(value)s</tfoot>', strip=True,
                               swallow_trailing_newline=True,
                               transform_newlines=False, replace_links=False,
                               replace_cosmetic=False)
bb_parser.add_simple_formatter('tr', '<tr>%(value)s</tr>', strip=True,
                               swallow_trailing_newline=True,
                               transform_newlines=False, replace_links=False,
                               replace_cosmetic=False)
bb_parser.add_simple_formatter('th', '<th>%(value)s</th>')
bb_parser.add_simple_formatter('td', '<td>%(value)s</td>')

bb_parser.add_simple_formatter('left', '<p style="text-align: left">%(value)s</p>')
bb_parser.add_simple_formatter('center', '<p style="text-align: center">%(value)s</p>')
bb_parser.add_simple_formatter('right', '<p style="text-align: right">%(value)s</p>')
bb_parser.add_simple_formatter('justify', '<p style="text-align: justify">%(value)s</p>')

bb_parser.add_simple_formatter('img', '<img src="%(value)s"/>', strip=True,
                               swallow_trailing_newline=True,
                               render_embedded=False,
                               transform_newlines=False, replace_links=False,
                               replace_cosmetic=False)
bb_parser.add_simple_formatter('icon', '<img src="%(value)s"/>', strip=True,
                               swallow_trailing_newline=True,
                               render_embedded=False,
                               transform_newlines=False, replace_links=False,
                               replace_cosmetic=False)


@_register_formatter('size')
def _bb_size_renderer(tag_name, value, options, parent, context):
    size = None
    if 'size' in options:
        size = options['size']
    style = ' style="size: {}"'.format(size) if size else ''
    return '<span{style}>{value}</span>'.format(**locals())


@_register_formatter('font')
def _bb_font_renderer(tag_name, value, options, parent, context):
    font = None
    if 'font' in options:
        font = options['font']
    style = ' style="font-family: {}"'.format(font) if font else ''
    return '<span{style}>{value}</span>'.format(**locals())


@_register_formatter('video', strip=True,
                     swallow_trailing_newline=True, render_embedded=False,
                     transform_newlines=False, replace_links=False,
                     replace_cosmetic=False)
def _bb_video_renderer(tag_name, value, options, parent, context):
    template = (
        '<iframe width="{width}" height="{height}" src="{src}" frameborder="0" '
        'allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" '
        'allowfullscreen></iframe>'
    )
    return template.format(
        width=options.get('width', '600px').split('px')[0] + 'px',
        height=options.get('height', '400px').split('px')[0] + 'px',
        src=value,
    )


DISK_FILE_ID_RE = re.compile('^n(\d+)$')


@_register_formatter('disk', standalone=True, render_embedded=False)
def _bb_disk_file_renderer(tag_name, value, options, parent, context):
    """ Рендерим [DISK FILE ID=n42] ссылкой на файл
    """
    disk_file_id = options.get('id', '')
    match = disk_file_id and DISK_FILE_ID_RE.match(disk_file_id)
    file_id = match and int(match.group(1))

    if not file_id:
        return '[ERROR: unrecognized file]'

    domain = context.get('BITRIX_DOMAIN')
    scheme = 'http' if context.get('BITRIX_NO_SSL', False) else 'https'

    if not domain:
        return '<a href="#" data-bitrix-file-id="%d">file</a>' % file_id

    return format_html(
        '<a href="{}" target="_blank">Click to download file</a>',
        '{}://{}/disk/showFile/{}/?ncc=1'.format(scheme, domain, file_id),
    )


@_register_formatter('user')
def _bb_user_renderer(tag_name, value, options, parent, context):
    user_id = None
    if 'user' in options:
        user_id = options['user']
    else:
        return value
    domain = context.get('BITRIX_DOMAIN')
    scheme = 'http' if context.get('BITRIX_NO_SSL', False) else 'https'
    if domain:
        return (
            '<a href="{scheme}://{domain}/company/personal/user/{user_id}/"'
            'target="_blank" data-bitrix-user-id="{user_id}">{value}</a>'
        ).format(**locals())
    return '<span data-bitrix-user-id={user_id}>{value}</span>' \
        .format(**locals())


def render_html(input_text, **context):
    """Принимает BB-код, возвращает HTML, учитывает специфику Битрикс24.

    На данные момент поддерживается практически все форматирование,
    кроме форматирования цитат ">>Цитата", т.к. это вообще не BB-код
    **context:
        BITRIX_DOMAIN (str) битрикс-домен, например 'b24.it-solution.ru'
        BITRIX_NO_SSL (bool) если коробка без https

    >>> render_html('[B]Hello, World![/B]')
    '<strong>Hello, World!</strong>'
    """
    if 'BITRIX_DOMAIN' not in context and hasattr(settings, 'PORTAL'):
        context['BITRIX_DOMAIN'] = settings.PORTAL
    return bb_parser.format(input_text, **context)


def strip(input_text, strip_newlines=False):
    """Принимает BB-код, отдает простой текст, из которого убраны теги
    >>> strip('[B]Hello, World![/B]')
    'Hello, World!'
    """
    return bb_parser.strip(input_text, strip_newlines=strip_newlines)


if __name__ == '__main__':
    import doctest

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    django.setup()
    doctest.testmod(verbose=True)
