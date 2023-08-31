from django.contrib import admin
from django.db import models
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from its_utils.app_currency.function import cbr
from its_utils.app_currency.signals import rates_updated


class ExchangeRate(models.Model):
    currency = models.ForeignKey('app_currency.Currency', related_name='exchange_rates', on_delete=models.PROTECT)
    date = models.DateField()
    value = models.FloatField()

    class Meta:
        unique_together = 'currency', 'date'

    class Admin(admin.ModelAdmin):
        list_display = 'currency', 'date', 'value'
        list_display_links = list_display

    def __str__(self):
        return '[{}] {}'.format(self.date, self.currency)

    def to_dict(self):
        return dict(
            currency=self.currency.code,
            date=self.date.isoformat(),
            value=self.value,
        )

    @classmethod
    def fill_latest(cls):
        rates = cbr.get_exchange_rate()
        date = timezone.localdate(parse_datetime(rates['Date']))

        db_date = cls.objects.aggregate(max_date=models.Max('date'))['max_date']
        if db_date and db_date >= date:
            return None

        cls._fill(rates, date)

        # Получили обновленные курсы - отправляем сигнал
        rates_updated.send(sender=cls, date=date)
        return date

    @classmethod
    def fill_from_archive(cls, date_from, date_to):
        while date_to >= date_from:
            rates = cbr.get_exchange_rate_archive(date_from)
            if rates:
                cls._fill(rates, date_from)

            date_from += timezone.timedelta(days=1)

    @classmethod
    def _fill(cls, rates, date):
        from its_utils.app_currency.models import Currency

        for code, data in rates['Valute'].items():
            name = data['Name']
            face_value = data['Nominal']
            value = data['Value']

            currency, _ = Currency.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'face_value': face_value,
                }
            )

            if face_value != currency.face_value:
                # В банке может поменяться номинал.
                # Поэтому для цеолстности данных,
                # значение пересчитывается по номиналу, который уже сохранен в базе.
                value *= currency.face_value / face_value

            rate, created = ExchangeRate.objects.get_or_create(
                currency=currency,
                date=date,
                defaults=dict(value=value),
            )

            if not created:
                rate.value = value
                rate.save()
