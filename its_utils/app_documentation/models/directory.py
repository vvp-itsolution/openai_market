# -*- coding: UTF-8 -*-

from django.db import models
from django.db.models.deletion import PROTECT
from mptt.models import MPTTModel, TreeForeignKey

from its_utils.functions2.get_model import get_model


class Directory(MPTTModel):
    name = models.CharField(max_length=255)
    parent = TreeForeignKey('self',
                            null=True,
                            blank=True,
                            related_name='children',
                            db_index=True, on_delete=PROTECT)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        app_label = 'app_documentation'

    @classmethod
    def get_dirs_with_articles(cls):
        article_model = get_model('app_documentation', 'Article')
        directories = list(cls.objects.all())
        articles = article_model.objects.filter(deleted=False)

        for directory in directories:
            directory.articles = [article
                                  for article in articles
                                  if article.directory == directory]

        return directories

    def __unicode__(self):
        return self.name
