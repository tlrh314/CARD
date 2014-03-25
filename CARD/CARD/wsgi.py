"""
WSGI config for CARD project on icto/fnwi server.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
import sys

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..','..'))
sys.path.insert(0,os.path.abspath(os.path.join(root_path,'/opt/virtualenv/card/lib/python2.7/site-packages')))
sys.path.insert(0, os.path.abspath(os.path.join(root_path,'card')))
sys.path.insert(0, os.path.abspath(os.path.join(root_path,'card','CARD')))

os.environ['DJANGO_SETTINGS_MODULE'] = 'CARD.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
