from django.db import models
from locations.models import Country


class Department(models.Model):
    title = models.CharField(max_length=100)
    leader = models.ForeignKey('Person', null=True, blank=True, related_name='lead_departments')
    
    def __unicode__(self):
        return self.title
    

class Occupation(models.Model):
    title = models.CharField(max_length=100)
    
    def __unicode__(self):
        return self.title
    

class Person(models.Model):
    name = models.CharField(max_length=255)                         # we won't use it in a summary report
    occupation = models.ForeignKey(Occupation)                      # we'll be able to group and to filter by both occupation and country
    department = models.ForeignKey(Department) # we'll be able to group and to filter by department and it leader
    country = models.ForeignKey(Country)
    birth_date = models.DateField()                                 # we'll be able to filter by year
    salary = models.DecimalField(max_digits=16, decimal_places=2)   # we'll sum and calculate average for salary and expenses 
    expenses = models.DecimalField(max_digits=16, decimal_places=2)
    
    def __unicode__(self):
        return self.name
