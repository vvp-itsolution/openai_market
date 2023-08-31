from django.utils.safestring import SafeData, mark_safe
"""Экранировние и форматирование BB-кода
"""


def bbcode_escape(input_text):
    """Так как никто пока не придумал нормального способа экранировать bbcode,
    видимо текст можно заэкранировать только костылями %(

    >>> bbcode_escape('''"Лариса" [/TABLE] 'Ивановна' ''')
    '“Лариса“ ⟦/TABLE⟧ ‘Ивановна‘ '
    >>> bbcode_escape(mark_safe('[b]Я жирный и безопасный[/b]'))
    '[b]Я жирный и безопасный[/b]'

    Проверил, что облачный битрикс24 нормально отображает данные юникод-замены.
    """
    if isinstance(input_text, SafeData):
        return input_text
    if not isinstance(input_text, str):
        input_text = str(input_text)
    return mark_safe(
        input_text
        .replace('[', '⟦').replace(']', '⟧')
        .replace('"', '“').replace("'", '‘')
    )


def bb_template(template, *t_args, **t_kwargs):
    """Микрошаблонизатор для построения bb-кода,
    форматирование с помощью str.format с автоэкранированием аргументов.

    >>> template_string = '''
    ... {h1}
    ... [TABLE]
    ...   [TR]
    ...     [TD]{}[/TD]
    ...     [TD]{}[/TD]
    ...     [TD]{last_name}[/TD]
    ...   [/TR]
    ... [/TABLE]'''.strip()
    >>> print(bb_template(template_string,
    ...                   '"Лариса"', '[/TABLE]', last_name="'Ивановна'",
    ...                   h1=mark_safe('[H1]Заголовок[/H1]')))
    [H1]Заголовок[/H1]
    [TABLE]
      [TR]
        [TD]“Лариса“[/TD]
        [TD]⟦/TABLE⟧[/TD]
        [TD]‘Ивановна‘[/TD]
      [/TR]
    [/TABLE]
    """
    return mark_safe(template.format(
        *(bbcode_escape(a) for a in t_args),
        **{k: bbcode_escape(v) for k, v in t_kwargs.items()}
    ))
