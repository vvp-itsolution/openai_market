from settings import ilogger


def view_error_500(request):
    # import logging
    # logger = logging.getLogger('django.request')
    # import sys
    # # ei = sys.exc_info()
    # # tb = sys.exc_traceback
    # try:
    #     logger.warning('ogogo error test', exc_info=1, extra={'request': {'aaa':'ewfwewefwef'}})
    #
    #     print internal_server_error
    #
    #
    # except:
    #     ei = sys.exc_info()
    #     pass
    #     #logger.warning('ogogo error test', exc_info=1, extra={'request': request})

    ilogger.error('view_error_500=>view_error_500_1')

    try:
        print(internal_server_error)
    except:
        ilogger.error('view_error_500=>view_error_500_2')
        raise
