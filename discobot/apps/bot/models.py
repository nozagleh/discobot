# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models

class Base(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=256)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Application(Base):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    client_id = models.CharField(max_length=200)
    client_secret = models.CharField(max_length=200,default='')

class Bot(Base):
    app = models.ForeignKey(
        'bot.Application',
        on_delete=models.CASCADE
    )
    token = models.CharField(max_length=200)

    def __str__(self):
        return self.name