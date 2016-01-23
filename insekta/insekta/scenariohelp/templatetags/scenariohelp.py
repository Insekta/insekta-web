from django import template

from insekta.scenariohelp.models import Question, get_num_unseen


register = template.Library()

@register.simple_tag
def num_new_questions(user):
    return get_num_unseen(user)


@register.simple_tag
def num_new_questions_answered(user):
    return Question.objects.filter(author=user, seen_by_author=False).count()