# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse

from .models import Application, Bot

# Create your views here.
def start(request):
    return HttpResponse("Starting bot")

def index(request):
    return HttpResponse("Hello")