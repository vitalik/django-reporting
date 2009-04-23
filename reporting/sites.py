from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import user_passes_test

def home(request):
    # TODO: reporting system home page shouldn't be blank :)
    from django.http import HttpResponse
    return HttpResponse()
home = user_passes_test(lambda u: u.is_staff)(home)

def wrap(report):
    def wrapper(request, *args, **kwargs):
        report_obj = report(request, *args, **kwargs)
        return report_obj.render_to_response()
    wrapper = user_passes_test(lambda u: u.is_staff)(wrapper)
    return wrapper

class ReportingSite(object):
    _registered_reports = []

    def register(self, report):
        # TODO: check that report parameter is a Report
        # instance, and has all required attributes, and
        # also check that another report with the same
        # name already exists
        self._registered_reports.append(report)

    def urls(self):
        urlpatterns = patterns('', url(r'^$', home))
        for report in self._registered_reports:
            urlpatterns += patterns('', url(r'^%s/$' % report.name, wrap(report)))
        return urlpatterns
    urls = property(urls)

site = ReportingSite()

