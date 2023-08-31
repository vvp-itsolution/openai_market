# -*- coding: UTF-8 -*-

from django.db import models
from django.utils import timezone


class Release(models.Model):

    DISABLED = 0
    TEST = 1
    PRODUCTION = 2

    STATE_CHOICES = (
        (DISABLED, 'Disabled'),
        (TEST, 'Test'),
        (PRODUCTION, 'Production')
    )

    application = models.ForeignKey('app_release.Application', on_delete=models.PROTECT)
    datetime = models.DateTimeField(default=timezone.now)
    comment = models.TextField(verbose_name=u'Описание', null=True, blank=True)
    state = models.SmallIntegerField(choices=STATE_CHOICES, default=TEST, verbose_name=u'Состояние')
    file = models.FileField(upload_to='release')

    def __str__(self):
        return u'%s %s %s' % (self.application, self.datetime, self.state)

    class Meta:
        app_label = 'app_release'

    @classmethod
    def get_release(cls, application_id, state):
        filter_ = dict(application_id=application_id)
        # проверяем является ли state итерируемой последовательностью
        if hasattr(state, '__iter__'):
            filter_.update(state__in=state)
        else:
            filter_.update(state=state)
        return cls.objects.filter(**filter_).order_by('-id').first()

    @classmethod
    def get_current_release(cls, application_id):
        return cls.get_release(application_id, cls.PRODUCTION)

    @classmethod
    def get_test_release(cls, application_id):
        return cls.get_release(application_id, cls.TEST)

    def __unicode__(self):
        return u'%s %s %s' % (self.application, self.datetime, self.state)
