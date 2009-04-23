import datetime

from django import forms
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.db.models.fields.related import ForeignKey
from django.db.models import Max, Min
from django.utils.html import escape

MONTH_NAMES = (
    _('January'),
    _('February'),
    _('March'),
    _('April'),
    _('May'),
    _('June'),
    _('July'),
    _('August'),
    _('September'),
    _('October'),
    _('November'),
    _('December'),
)

class ValueField(unicode):
    # Hack to let template know if the field is a value
    # to align right, and format as number
    def __init__(self, value):
        self.value = value

    def __unicode__(self):
        return self.value

    def is_value(self):
        return True

class Report(object):
    list_raw = []

    def __init__(self, request):
        self.request = request

    def _get_field(self, field):
        return self.model._meta.get_field(field)

    def _get_group_by(self):
        group_by = self.request.GET.get('group', None)
        if group_by not in self.list_group:
            group_by = None
        if not group_by and not None in self.list_group:
            group_by = self.list_group[0]
        return group_by

    def _get_headers(self):
        fields = list(self.list_raw)
        group_by = self._get_group_by()
        if group_by:
            fields.append(group_by)
        for item in self.list_values:
            fields.append(item[0])
        order = self.request.GET.get('order', None)
        args = []
        for key, value in self.request.GET.iteritems():
            if key != 'order':
                args.append('%s=%s' % (key, value))

        headers = []
        for field in fields:
            if order and order == '-' + field:
                order_field = field
            else:
                order_field = '-%s' % field
            link = self.request.META['PATH_INFO'] + \
                '?' + '&'.join(args + ['order=%s' % order_field])
            headers.append({
                'field': field,
                'verbose_name': self._get_field(field).verbose_name,
                'link': link,
            })
        return headers

    def _get_results_dict(self):
        qs = self.model.objects.all()
        for filter_field in self.list_filter:
            filter_value = self.request.GET.get(filter_field, None)
            if filter_value:
                qs = qs.filter(**{filter_field: filter_value})

        annotate = {}
        for field, func in self.list_values:
            annotate[field] = func(field)

        values = list(self.list_raw)
        group_by = self._get_group_by()
        if group_by:
            values.append(group_by)

        order = self.request.GET.get('order', values[0])

        res = qs.values(*values).annotate(**annotate).order_by(order)
        return res

    def _get_name_for_id(self, field_name, data):
        id = data[field_name]
        field = self._get_field(field_name)
        if isinstance(field, ForeignKey):
            rel_model = field.rel.to
            try:
                obj = rel_model.objects.get(id=id)
            except rel_model.DoesNotExist:
                name = _('N/A')
            else:
                name = unicode(obj)
        else:
            name = id
        return name

    def _get_results(self):
        qs = self._get_results_dict()
        results = []
        for row in qs:
            result_row = []
            for raw_col in self.list_raw:
                result_row.append(self._get_name_for_id(raw_col, row))
            group_by = self._get_group_by()
            if group_by:
                result_row.append(self._get_name_for_id(group_by, row))
            for field, func in self.list_values:
                result_row.append(ValueField(row[field]))
            results.append(result_row)
        return results

    def _get_filter_form(self):
        class FilterForm(forms.ModelForm):
            class Meta:
                model = self.model
                fields = self.list_filter

        def dropdown(field_name, verbose_name, name_list, value_list, selected_value):
            options_html = '<option value="">---------</option>'
            for name, value in zip(name_list, value_list):
                # selected
                selected = ''
                if selected_value and (value == selected_value):
                    selected = ' selected="selected"'
                # options
                options_html += '<option value="%s"%s>%s</option>' % (
                    value,
                    selected,
                    name,
                )
            result = '''
                <li>
                    <label for="id_%(field_name)s">%(verbose_name)s</label>
                    <select name="%(field_name)s" id="id_%(field_name)s">
                        %(options_html)s
                    </select>
                </li>
            ''' % dict(
                field_name=field_name,
                verbose_name=verbose_name,
                options_html=options_html,
            )
            return result

        form_html = ''
        for filter in self.list_filter:
            if '__' in filter:
                field_name, opt = filter.split('__')
                field = self._get_field(field_name)
                verbose_name = unicode(field.verbose_name).capitalize()
                selected = self.request.GET.get(filter, '')
                if opt == 'year':
                    first_year = self.model.objects.aggregate(Min(field_name))['%s__min' % field_name].year
                    last_year = self.model.objects.aggregate(Max(field_name))['%s__max' % field_name].year
                    name_list = value_list = xrange(first_year, last_year + 1)
                    try:
                        selected_value = int(self.request.GET.get(filter, None))
                    except (ValueError, TypeError):
                        selected_value = None
                    form_html += dropdown(filter, verbose_name + ' year', name_list, value_list, selected_value)
                elif opt == 'month':
                    name_list = [unicode(month) for month in MONTH_NAMES] # to get translation
                    value_list = xrange(1, len(MONTH_NAMES))
                    try:
                        selected_value = int(self.request.GET.get(filter, None))
                    except (ValueError, TypeError):
                        selected_value = None
                    form_html += dropdown(filter, verbose_name + ' month', name_list, value_list, selected_value)
                elif opt == 'day':
                    name_list = value_list = xrange(1, 31)
                    try:
                        selected_value = int(self.request.GET.get(filter, None))
                    except (ValueError, TypeError):
                        selected_value = None
                    form_html += dropdown(filter, verbose_name + ' day', name_list, value_list, selected_value)

        data = dict(self.request.GET)
        for key, value in data.iteritems():
            data[key] = value[0]
        form = FilterForm(initial=data)
        form_html += form.as_ul()
        return mark_safe(form_html)

    def _get_group_select(self):
        group_by = self.request.GET.get('group', None)
        html = '<select id="group" name="group">\n'
        for field in self.list_group:
            if field == group_by:
                selected = ' selected="selected"'
            else:
                selected = ''
            if field:
                html += '<option value="%s"%s>%s</option>\n' % (
                    field,
                    selected,
                    unicode(self._get_field(field).verbose_name).title(),
                )
            else:
                html += '<option value="">---------</option>'
        html += '</select>\n'
        return mark_safe(html)

    def url(cls):
        params = ''
        if hasattr(cls, 'default_filters'):
            params = '?' + '&'.join(['%s=%s' % (key, escape(value)) for key, value in cls.default_filters.iteritems()])
        return '/reporting/%s/%s' % (cls.name, params)
    url = classmethod(url)

    def render_to_response(self):
        context = {}
        context['title'] = self.verbose_name
        context['report_name'] = self.verbose_name
        context['result_headers'] = self._get_headers()
        context['results'] = self._get_results()
        context['group_select'] = self._get_group_select()
        context['filter_form'] = self._get_filter_form()
        return render_to_response('reporting/report.html', context)

