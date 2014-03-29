# https://stackoverflow.com/questions/17148544/django-template-dynamic-variable-name
from django import template

register = template.Library()

# Lookup value of 2D-array with string key identifiers.
def lookup(object, key1, key2):
    return object[key1][key2]

# Lookup using a variable
#def lookup(object, property):
    #return getattr(object, property)

register.simple_tag(lookup)
