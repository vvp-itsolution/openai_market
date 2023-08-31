from django.contrib import admin
from django.db import models


class BaseApplication(models.Model):
    api_id = models.IntegerField()
    api_hash = models.CharField(max_length=32)

    class Meta:
        abstract = True

    class Admin(admin.ModelAdmin):
        pass

    def __str__(self):
        return str(self.api_id)
