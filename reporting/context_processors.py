from sites import site

def report_list(request):
    return {'report_list': site._registered_reports}

