import json
import re

ESCAPE_QUOTES_FIND_PATTERN = r'escape_quotes_start(.+?)escape_quotes_end'
ESCAPE_QUOTES_SUB_PATTERN = r'(escape_quotes_start.+?escape_quotes_end)'
ESCAPE_QUOTES_TOKEN = '__ESCAPE_QUOTES_TOKEN__'


def escape_quotes(json_str):
    """
    Экранировать кавычки в json-строках
    Экранируются участки, которые заключены между `escape_quotes_start` и `escape_quotes_end`
    пример:
    >>> s = '{"a": "escape_quotes_startValue "with" unescaped quotesescape_quotes_end"}'
    >>> escape_quotes(s)
    '{"a": "Value \\"with\\" unescaped quotes"}'
    """

    unescaped_strings = re.findall(ESCAPE_QUOTES_FIND_PATTERN, json_str)
    tokened_json = re.sub(ESCAPE_QUOTES_SUB_PATTERN, ESCAPE_QUOTES_TOKEN, json_str)

    escaped_json = tokened_json
    for unescaped_str in unescaped_strings:
        escaped_json = escaped_json.replace(
            ESCAPE_QUOTES_TOKEN, unescaped_str.replace('"', '\\"'), 1
        )

    return escaped_json


def parse_json_with_escape_quotes(json_str):
    """
    Парсинг json с неэкранированными кавычками
    """
    escaped_json = escape_quotes(json_str)
    return json.loads(escaped_json)
