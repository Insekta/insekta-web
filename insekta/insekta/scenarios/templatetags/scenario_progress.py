from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def scenario_progress(num_submitted, num_available):
    unsolved_dot = ('<img src="{}scenarios/images/unsolved.png" alt="O" '
                    'title="Unsolved">').format(settings.STATIC_URL)
    solved_dot = ('<img src="{}scenarios/images/solved.png" alt="X" '
                  'title="Solved">').format(settings.STATIC_URL)

    num_missing = num_available - num_submitted
    return mark_safe(solved_dot * num_submitted + unsolved_dot * num_missing)


scenario_progress.is_safe = True
