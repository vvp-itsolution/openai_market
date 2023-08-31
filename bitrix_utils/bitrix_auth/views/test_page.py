# -*- coding: UTF-8 -*-

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from bitrix_utils.bitrix_auth.functions.dec_bitrix_start_point import bitrix_start_point


@csrf_exempt
@bitrix_start_point
def test_page(request):

    return render(request, 'bitrix_auth/test_page.html', {'bx_user': request.bx_user})
