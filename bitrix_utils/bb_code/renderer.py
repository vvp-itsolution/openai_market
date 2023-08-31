from configparser import NoOptionError

import html2bbcode.parser


_missing = object()


class Renderer(html2bbcode.parser.HTML2BBCode):

    def error(self, message):
        raise ValueError(message)

    def __init__(self):
        super().__init__()
        # Для специфики переводов строк в BB Б24
        self._set_config_option('p', 'start', '')
        self._set_config_option('b', 'start', '[b]')
        self._set_config_option('b', 'end', '[/b]')

    def _get_config_option(self, section: str, option: str, default=_missing):
        try:
            return self.config.get(section, option)
        except NoOptionError:
            if default is _missing:
                raise
            return default

    def _set_config_option(self, section, option, value=None):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)


default_renderer = Renderer()


def html_to_bb(
        html: str,
        renderer: html2bbcode.parser.HTML2BBCode = default_renderer,
        strip_whitespace: bool = True,
) -> str:
    r"""Парсит html, возвращает BB-code

    Для работы требуется pip install html2bbcode==2.3.2

    >>> html_to_bb('<ul><li>one</li><li>two</li></ul>')
    '[list][li]one[/li][li]two[/li][/list]'

    >>> html_to_bb('<a href="http://google.com/">Google</a>')
    '[url=http://google.com/]Google[/url]'

    >>> html_to_bb('<img src="http://www.google.com/images/logo.png">')
    '[img]http://www.google.com/images/logo.png[/img]'

    >>> html_to_bb('<em>EM test</em>')
    '[i]EM test[/i]'

    >>> html_to_bb('<strong>Strong text</strong>')
    '[b]Strong text[/b]'

    >>> html_to_bb('<code>a = 10;</code>')
    '[code]a = 10;[/code]'

    >>> html_to_bb('<blockquote>Beautiful is better than ugly.</blockquote>')
    '[quote]Beautiful is better than ugly.[/quote]'

    >>> html_to_bb('<font face="Arial">Text decorations</font>')
    '[font=Arial]Text decorations[/font]'

    >>> html_to_bb('<font size="2">Text decorations</font>')
    '[size=2]Text decorations[/size]'

    >>> html_to_bb('<font color="red">Text decorations</font>')
    '[color=red]Text decorations[/color]'

    >>> html_to_bb('<font face="Arial" color="green" size="2">Text decorations</font>')
    '[color=green][font=Arial][size=2]Text decorations[/size][/font][/color]'

    >>> html_to_bb('Text<br>break')
    'Text\nbreak'

    >>> html_to_bb('&nbsp;')
    '\xa0'

    >>> html_to_bb('<p>one\ntwo</p><p>three</p>')
    'one two\nthree\n'
    """
    if strip_whitespace:
        html = ' '.join(html.split())
    return str(renderer.feed(html))


if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False)
