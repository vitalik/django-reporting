import reporting
from django.db.models import Sum, Avg, Count
from models import Person

class PersonReport(reporting.Report):
    model = Person
    verbose_name = 'Person Report'
    annotate = (
        ('id', Count, 'Total'),
        ('salary', Sum),
        ('expenses', Sum),
    )
    aggregate = (
        ('id', Count, 'Total'),
        ('salary', Sum, 'Salary'),
        ('expenses', Sum, 'Expenses'),
    )
    group_by = [
        'department',
        'department__leader', 
        'occupation', 
    ]
    list_filter = [
       'occupation',
       'country',
    ]
    
    detail_list_display = [
        'name', 
        'salary',
        'expenses', 
    ]

    date_hierarchy = 'birth_date'


reporting.register('people', PersonReport)