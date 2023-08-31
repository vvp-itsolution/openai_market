# coding=utf-8
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.template.response import TemplateResponse

from settings import ilogger


def view_error_403(request):

    ilogger.error('view_error_403', 'view_error_403')
    raise PermissionDenied("Нет токена")
