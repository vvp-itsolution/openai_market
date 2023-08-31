# -*- coding: UTF-8 -*-


from django.test import TestCase
from django.contrib.auth.models import User

from its_utils.app_documentation.models import Article


class ArticleTestCase(TestCase):

    def setUp(self):
        User.objects.create(pk=1,
                            username='admin',
                            password='123')
        Article.objects.create(title='TestArticle',
                               user_id=1)

    def test_secret_key(self):
        article = Article.objects.get(title='TestArticle')
        self.assertIsInstance(article.secret_key, str)
        self.assertEqual(len(article.secret_key), 12)
