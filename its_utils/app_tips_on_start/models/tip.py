# -*- coding: utf-8 -*-
import requests
import six
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.templatetags.static import static
from froala_editor.fields import FroalaField

try:
    from its_logger import its_logger as ilogger
except ImportError:
    from settings import ilogger

if not six.PY2:
    from typing import Optional


@six.python_2_unicode_compatible
class Tip(models.Model):
    KDB_API_BASE = 'https://kdb24.ru'
    KDB_API_T = KDB_API_BASE + '/api/v1/article.get.collection/{secret}/?js=false'
    WRAPPER_CLASS = 'fr-view'

    category = models.ForeignKey(
        to='TipCategory',
        verbose_name=u'категория',
        on_delete=models.PROTECT,
    )

    kdb_article_secret = models.CharField(
        'секрет статьи из базы знаний',
        max_length=255,
        default='',
        blank=True,
        help_text='Заменяет текст и название статьи на статью из Базы Знаний. '
                  'Код можно посмотреть, зайдя в доступную для редактирования '
                  'статью и нажав "Получить HTML код ..." в модалке со ссылкой. '
                  'Пример: 58889_BIDw5EybDJJGT4Ivawn33nLQved7Mc3Dgy2kMBZv9H',
    )

    title = models.CharField(u'заголовок', max_length=255)
    active = models.BooleanField(u'активна', default=True)
    body = FroalaField(u'тело')

    sort = models.IntegerField(
        default=500,
        verbose_name=u'приоритет',
        help_text='подсказки с большим приоритетом отображаются раньше '
                  'подсказок с меньшим приоритетом. При равенстве приоритетов '
                  'порядок подсказок случайный',
    )

    class Meta:
        verbose_name = u'подсказка при старте'
        verbose_name_plural = u'подсказки при старте'
        unique_together = ('category', 'title')
        ordering = ['-sort', '?']

    def __str__(self):
        return u'[{0.category.title}] {0.title}'.format(self)

    class Admin(admin.ModelAdmin):
        list_display = ('id', 'category', 'kdb_article_secret',
                        'title', 'active', 'sort',)
        list_display_links = 'id', 'category',
        list_select_related = 'category',
        search_fields = ('id', 'category__id', 'title',
                         'kdb_article_secret',
                         'body', 'category__title',)
        list_editable = 'sort', 'title', 'active',
        list_filter = 'category', 'active',
        preserve_filters = True

        class Media:
            css = dict(all=[static('app_tips_on_start/admin.css')])

    def save(self, fetch_from_kdb=True, *args, **kwargs):
        if self.kdb_article_secret.startswith('kdb_'):
            self.kdb_article_secret = \
                self.kdb_article_secret.rsplit('kdb_', 1)[-1]
        super(Tip, self).save(*args, **kwargs)

        if fetch_from_kdb:
            self.get_from_kdb(update_self=True)

    def get_from_kdb(self, update_self=True):
        # type: (bool) -> Optional[dict]
        """получение статьи по секрету из kdb24.ru
        """
        if not self.kdb_article_secret:
            return None

        if 'articles' in settings.INSTALLED_APPS:  # kdb
            # Внутри kdb нет смысла делать запросы через requests
            from articles.api.article.get_collection import get_article, as_json
            try:
                article = get_article(self.kdb_article_secret)
            except ObjectDoesNotExist:
                return None
            article = as_json(article)

        else:
            url = self.KDB_API_T.format(secret=self.kdb_article_secret)
            try:
                article = requests.get(url).json()
            except requests.RequestException as e:
                ilogger.error('get_kdb_article_error', str(e))
                return None

        if update_self and (
                self.title != article['title'] or self.body != article['body']):
            self.title = article['title']
            self.body = article['body']
            self.save(fetch_from_kdb=False, update_fields=['title', 'body'])

        return article

    def dict(self, update_self=True):
        # type: (bool) -> dict
        article = self.get_from_kdb(update_self=update_self)
        if article is not None:
            article['html'] = article.pop('body')
        else:
            article = dict(
                title=self.title,
                html=self.body,
                styles=[
                    static('froala_editor/css/froala_editor.pkgd.min.css'),
                ],
                wrapperClass=self.WRAPPER_CLASS,
            )

        return dict(
            category=self.category.title,
            sort=self.sort,
            **article
        )
