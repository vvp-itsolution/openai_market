# -*- coding: UTF-8 -*-


from django.contrib.auth import logout
from django.shortcuts import redirect
#from django.core.urlresolvers import reverse


def view_logout_user(request):
    logout(request)
    return redirect(reverse('main_article'))
