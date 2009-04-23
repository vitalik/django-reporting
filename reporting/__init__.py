import imp

from django.conf import settings
from reports import Report
from sites import site

REPORTING_SOURCE_FILE = 'reporting'

def autodiscover():
    # Check django/contrib/admin/__init__.py to know what I'm doing :)
    for app in settings.INSTALLED_APPS:
        try:
            app_path = __import__(app, {}, {}, [app.split('.')[-1]]).__path__
        except AttributeError:
            continue

        try:
            imp.find_module(REPORTING_SOURCE_FILE, app_path)
        except ImportError:
            continue

        __import__('%s.%s' % (app, REPORTING_SOURCE_FILE))

