# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Application, Bot
# Register your models here.
admin.site.register(Application)
admin.site.register(Bot)