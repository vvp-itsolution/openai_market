# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import AssetsFile, AssetsPicture


@admin.register(AssetsFile)
class FileAdmin(admin.ModelAdmin):
    list_display = 'id', 'name', 'file', 'created', 'updated',
    list_display_links = 'id', 'name', 'file', 'created', 'updated',


@admin.register(AssetsPicture)
class PictureAdmin(admin.ModelAdmin):
    list_display = 'id', 'name', 'picture', 'created', 'updated',
    list_display_links = 'id', 'name', 'picture', 'created', 'updated',
