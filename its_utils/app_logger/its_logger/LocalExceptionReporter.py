from django.views.debug import ExceptionReporter
from django.template import Context, Engine
from pathlib import Path
CURRENT_DIR = Path(__file__).parent.parent
DEBUG_ENGINE = Engine(
    debug=True,
    libraries={'i18n': 'django.templatetags.i18n'},
)

class LocalExceptionReporter(ExceptionReporter):

    def get_traceback_html(self):
        """Return HTML version of debug 500 HTTP error page."""
        with Path(CURRENT_DIR, 'templates', 'technical_500.html').open(encoding='utf-8') as fh:
            t = DEBUG_ENGINE.from_string(fh.read())
        c = Context(self.get_traceback_data(), use_l10n=False)
        return t.render(c)