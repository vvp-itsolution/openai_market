from django.contrib import admin
from django.db import models
from django.utils import timezone


class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    face_value = models.IntegerField(blank=True, default=1)

    class Admin(admin.ModelAdmin):
        list_display = 'code', 'name'
        list_display_links = list_display

    @classmethod
    def get_defaults(cls):
        return cls.objects.filter(models.Q(code='USD') | models.Q(code='EUR'))

    def __str__(self):
        return u'{}: {} {}'.format(self.code, self.face_value, self.name)

    def get_rate(self, date: timezone.datetime.date = None) -> float:
        rates = self.exchange_rates

        if date:
            rates = rates.filter(date__lte=date)

        return rates.order_by('date').last()
