from django.contrib import admin
from django.db import models


class BaseEntity(models.Model):
    """
    Для DjangoSession (хранение entity_hash)
    """

    session = models.ForeignKey('TelethonSession', on_delete=models.CASCADE)
    entity_id = models.BigIntegerField()
    hash_value = models.BigIntegerField()
    username = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True, editable=True)

    class Meta:
        abstract = True
        index_together = (
            ('session', 'entity_id'),
            ('session', 'username'),
            ('session', 'phone'),
            ('session', 'name'),
        )

    class Admin(admin.ModelAdmin):
        raw_id_fields = 'session',

    def __str__(self):
        return '[{}] {} {}'.format(self.entity_id, self.name or '', self.username or '').strip()
