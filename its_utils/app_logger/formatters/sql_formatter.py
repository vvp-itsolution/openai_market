import logging
import sys


class SqlFormatter(logging.Formatter):
    """Логгинг sql-запросов при разработке

    Usage:
        # Установка зависимостей, без них не будет форматирования и подсветки
        $ pip install pygments sqlparse
        $ pip install pygments==2.5.2 sqlparse==0.3.0  # проверено с этими версиями

        # В settings.py:
        from django.utils.log import DEFAULT_LOGGING
        LOGGING = DEFAULT_LOGGING
        LOGGING['formatters'].update({
            'sql': {
                '()': 'its_utils.app_logger.formatters.SqlFormatter',
                'format': '[%(duration).3f] %(statement)s',
            },
        })
        LOGGING['handlers'].update({
            'sql': {
                'class': 'logging.StreamHandler',
                'filters': ['require_debug_true'],
                'level': 'DEBUG',
                'formatter': 'sql',
            },
        })
        LOGGING['loggers'].update({
            'django.db.backends': {
                'level': 'DEBUG',
                'handlers': ['sql'],
                'propagate': False,
            },
        })
    """
    def format(self, record):
        # Check if Pygments is available for coloring
        try:
            import pygments
            from pygments.lexers import SqlLexer
            from pygments.formatters import TerminalTrueColorFormatter
        except ImportError as e:
            print(e, file=sys.stderr)
            pygments = None

        # Check if sqlparse is available for indentation
        try:
            import sqlparse
        except ImportError as e:
            print(e, file=sys.stderr)
            sqlparse = None

        # Remove leading and trailing whitespaces
        sql = record.sql.strip()

        if sqlparse:
            # Indent the SQL query
            sql = sqlparse.format(sql, reindent=True)

        if pygments:
            # Highlight the SQL query
            sql = pygments.highlight(
                sql,
                SqlLexer(),
                TerminalTrueColorFormatter(style='native')
            )

        # Set the record's statement to the formatted query
        record.statement = sql
        try:
            record.duration = float(record.duration)
        except (AttributeError, TypeError, ValueError):
            record.duration = float('nan')
        return super(SqlFormatter, self).format(record)
