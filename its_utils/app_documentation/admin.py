# -*- coding: UTF-8 -*-


from django.contrib import admin
#from django.core.urlresolvers import reverse
from mptt.admin import MPTTModelAdmin

from .models import Article, Diff, Category, Image, Directory


class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'pk', 'slug', 'user', 'git_url', 'created', 'edited', 'is_available', 'read_link']
    exclude = ['slug']
    readonly_fields = ['rendered_body']
    date_hierarchy = 'created'
    ordering = ['-edited']
    raw_id_fields = ['user']

    def read_link(self, obj):
        url = ""#reverse('article_read', args=[obj.pk])
        return '<a href="%s?key=%s" target="_blank">Прочитать</a>' % (url, obj.secret_key)

    read_link.allow_tags = True
    read_link.short_description = 'Share'


class DiffAdmin(admin.ModelAdmin):
    list_display = ['article', 'user', 'created']
    readonly_fields = ['article', 'user', 'created', 'body', 'data']
    date_hierarchy = 'created'
    raw_id_fields = 'user',


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


class ImageAdmin(admin.ModelAdmin):
    list_display = ['article', 'image_tag']
    ordering = ['article']
    # readonly_fields = ['article', 'source_img']


admin.site.register(Article, ArticleAdmin)
admin.site.register(Diff, DiffAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Directory, MPTTModelAdmin)
