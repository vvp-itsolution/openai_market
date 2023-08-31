# -*- coding: utf-8 -*-
from django.contrib import admin

from . import models


admin.site.register(models.Tip, models.Tip.Admin)
admin.site.register(models.TipCategory, models.TipCategory.Admin)
