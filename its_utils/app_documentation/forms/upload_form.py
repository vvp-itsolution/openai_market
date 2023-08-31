# -*- coding: UTF-8 -*-

from django import forms


class UploadForm(forms.Form):
    image = forms.ImageField(
        label='Выберите изображение')
