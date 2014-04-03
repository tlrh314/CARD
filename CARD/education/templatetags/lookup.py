# https://stackoverflow.com/questions/17148544/django-template-dynamic-variable-name
from django import template

register = template.Library()

def lookup(object, key1, key2=None, number=None):
    if not key2 and not number:
        # Lookup value of dictionary
        return object[key1]
    elif not number:
        # Lookup value of 2D-array with string key identifiers.
        return object[key1][key2]
    else:
        # Unpack tuple in 2D-array with string key identifiers.
        value1, value2 = object[key1][key2]
        if number == '0':
            return value1
        elif number == '1':
            return value2
        else:
            return None



# Lookup using a variable
#def lookup(object, property):
    #return getattr(object, property)

register.simple_tag(lookup)
