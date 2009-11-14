from django.contrib import admin
from models import Department, Occupation, Person

class PersonAdmin(admin.ModelAdmin):
    list_display = ['name', 'occupation', 'department', 'country', 'birth_date', 'salary', 'expenses']

admin.site.register(Person, PersonAdmin)
admin.site.register([Department, Occupation])