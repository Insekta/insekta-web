from django import template
from django.utils.safestring import mark_safe


register = template.Library()

@register.simple_tag
def format_user(user):
    if user.first_name:
        if user.last_name:
            name = '{} {}'.format(user.first_name, user.last_name)
        else:
            name = user.first_name
    else:
        name = user.username

    return mark_safe(('<span class="user">'
                      '<span class="glyphicon glyphicon-user"></span> {}</span>'
                      '</span>').format(name))
