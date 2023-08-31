from its_utils.app_logger.its_logger.logger_thread_local import set_request_start_time

# try:
#     from django.utils.deprecation import MiddlewareMixin
# except ImportError:
#     MiddlewareMixin = object
from django.utils.deprecation import MiddlewareMixin


class LoggerThreadLocalMiddleware(MiddlewareMixin):

    def process_request(self, request):
        set_request_start_time()

