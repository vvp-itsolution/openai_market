# -*- coding: UTF-8 -*-
from django.db.models.deletion import PROTECT
from unidecode import unidecode

from its_utils.app_documentation.documentation_settings import ITS_UTILS_DOCUMENTATION
from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.encoding import smart_text

import markdown

from .diff import Diff
from .directory import Directory


def create_secret_key():
    return User.objects.make_random_password(length=12)


class Article(models.Model):
    user = models.ForeignKey(User, on_delete=PROTECT)
    directory = models.ForeignKey(Directory, default=1, on_delete=PROTECT)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=511)

    body = models.TextField(default='')
    rendered_body = models.TextField(default='', editable=False)

    github_url = models.CharField(max_length=2000, blank=True, default='')
    auto_fetched = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=31, blank=True, default=create_secret_key)

    deleted = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'app_documentation'

    def save(self, *args, **kwargs):
        try:
            old_body = Article.objects.get(pk=self.pk).body
        except models.ObjectDoesNotExist:
            old_body = ''

        self.title = smart_text(self.title)
        self.body = smart_text(self.body)

        self.slug = slugify(unidecode(self.title))
        self.rendered_body = self.render(self.body)

        super(Article, self).save(*args, **kwargs)
        self.diff = Diff.add_new_and_get_diff(
            user=self.user, article=self, old_body=old_body, body=self.body)

    def is_available(self):
        return not self.deleted

    is_available.boolean = True
    is_available.short_description = 'Available?'

    def git_url(self):
        return '<a href={0}>{0}</a>'.format(self.github_url)

    git_url.allow_tags = True

    @classmethod
    def get_body(cls, pk, rendered=False):
        if rendered:
            col = 'rendered_body'
        else:
            col = 'body'

        return cls.objects.values_list(col, flat=True).get(pk=pk)

    @staticmethod
    def render(text):
        extensions = ITS_UTILS_DOCUMENTATION.get('MARKDOWN_EXTENSIONS', [])
        safe_mode = ITS_UTILS_DOCUMENTATION.get('SAFE_MARKDOWN', 'escape')

        return markdown.markdown(text, extensions=extensions, safe_mode=safe_mode)

    def __unicode__(self):
        return smart_text('%s. %s' % (self.pk, self.title))
