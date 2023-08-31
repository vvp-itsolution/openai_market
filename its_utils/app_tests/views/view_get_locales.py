#coding=utf-8
import json
from django.http import HttpResponse



def view_get_locales(request):
    if not request.user.is_superuser:
        #TODO переделать
        return 3
    import locale
    import sys
    loc_info = {'loc_loc': locale.getlocale(), 'loc_def': locale.getdefaultlocale(), 'sys_fenc': sys.getfilesystemencoding(), 'sys_denc': sys.getdefaultencoding()}
    return HttpResponse(json.dumps(loc_info))