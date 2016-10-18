from django import template

register = template.Library()

@register.filter
def list_elem(my_list,pos):
    return my_list[pos]
