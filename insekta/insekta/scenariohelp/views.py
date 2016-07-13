import bleach

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from insekta.base.utils import describe_allowed_markup
from insekta.scenariohelp.forms import NewQuestionForm
from insekta.scenariohelp.models import SupportedScenario, Question, SeenQuestion, Post
from insekta.scenarios.models import Course, Scenario


NUM_SOLVED_PER_PAGE = 25


@login_required
def list_questions(request):

    supported_scenarios = SupportedScenario.objects.filter(user=request.user)
    scenario_pks = [s.scenario.pk for s in supported_scenarios]

    questions = (Question.objects.select_related()
                 .filter(is_solved=False, scenario__pk__in=scenario_pks)
                 .order_by('-time_created'))
    questions = list(questions)
    _annotate_is_seen(questions, request.user)

    return render(request, 'scenariohelp/list_questions.html', {
        'questions': questions,
        'active_nav': 'help'
    })


@login_required
def my_questions(request):
    questions = (Question.objects.select_related().filter(author=request.user)
                 .order_by('-time_created'))
    return render(request, 'scenariohelp/my_questions.html', {
        'questions': questions,
        'active_nav': 'account'
    })


@login_required
def scenario_questions(request, course_key, scenario_key):
    scenario = get_object_or_404(Scenario, key=scenario_key)
    course = get_object_or_404(Course, key=course_key)
    if not scenario.is_inside_course(course):
        raise Http404('No such scenario in this course.')
    unsolved_questions = list(Question.objects.select_related()
                              .filter(is_solved=False, scenario=scenario)
                              .order_by('-time_created'))
    my_unsolved = []
    others_unsolved = []
    for question in unsolved_questions:
        if question.author == request.user:
            my_unsolved.append(question)
        else:
            others_unsolved.append(question)

    _annotate_is_seen(others_unsolved, request.user)

    solved_questions = (Question.objects.select_related()
                        .filter(is_solved=True, scenario=scenario)
                        .order_by('-time_created'))
    paginator = Paginator(solved_questions, per_page=NUM_SOLVED_PER_PAGE)
    try:
        solved_page = paginator.page(request.GET.get('page'))
    except InvalidPage:
        solved_page = paginator.page(1)

    return render(request, 'scenariohelp/scenario_questions.html', {
        'course': course,
        'scenario': scenario,
        'my_unsolved': my_unsolved,
        'others_unsolved': others_unsolved,
        'solved_page': solved_page,
        'active_nav': None
    })


@login_required
def new_question(request, course_key, scenario_key):
    scenario = get_object_or_404(Scenario, key=scenario_key, enabled=True)
    course = get_object_or_404(Course, key=course_key)
    if not scenario.is_inside_course(course):
        raise Http404('No such scenario in this course.')

    preview = ''
    if request.method == 'POST':
        form = NewQuestionForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            preview = bleach.clean(bleach.linkify(text),
                                   tags=settings.TAG_WHITELIST,
                                   attributes=settings.ATTR_WHITELIST)

            if 'save' in request.POST:
                question = Question.objects.create(
                    title=form.cleaned_data['title'],
                    author=request.user,
                    course=course,
                    scenario=scenario)
                question.post_answer(request.user, preview, question.time_created)
                messages.success(request, _('Question was saved.'))
                return redirect('scenariohelp:scenario_questions', course.key, scenario.key)

    else:
        form = NewQuestionForm()

    allowed_markup = describe_allowed_markup(settings.TAG_WHITELIST,
                                             settings.ATTR_WHITELIST)
    return render(request, 'scenariohelp/new_question.html', {
        'course': course,
        'scenario': scenario,
        'form': form,
        'preview': preview,
        'allowed_markup': allowed_markup,
        'active_nav': None
    })


@login_required
def view_question(request, question_pk):
    question = get_object_or_404(Question, pk=question_pk)
    question.mark_seen(request.user)
    posts = Post.objects.filter(question=question).select_related()

    answer = ''
    answer_preview = ''
    if request.method == 'POST':
        if 'solve' in request.POST and question.author == request.user:
            question.is_solved = True
            question.save()
            return redirect('scenariohelp:my_questions')

        answer = request.POST.get('answer', '')
        answer_preview = bleach.clean(bleach.linkify(answer),
                                      tags=settings.TAG_WHITELIST,
                                      attributes=settings.ATTR_WHITELIST)
        if 'save' in request.POST:
            if not question.is_solved:
                question.post_answer(request.user, answer_preview)
                return redirect('scenariohelp:view', question.pk)

    is_own = question.author == request.user
    allowed_markup = describe_allowed_markup(settings.TAG_WHITELIST,
                                             settings.ATTR_WHITELIST)
    return render(request, 'scenariohelp/view_question.html', {
        'question': question,
        'posts': posts,
        'answer': answer,
        'answer_preview': answer_preview,
        'allowed_markup': allowed_markup,
        'is_own': is_own,
        'active_nav': 'account' if is_own else 'help',
        'src': request.GET.get('src', 'scenario')
    })


@login_required
def configure_help(request):
    supported_scenario_pks = set()
    for supported in SupportedScenario.objects.filter(user=request.user):
        supported_scenario_pks.add(supported.scenario.pk)

    scenarios = list(Scenario.objects.filter(enabled=True).order_by('title'))
    for scenario in scenarios:
        scenario.is_supported = scenario.pk in supported_scenario_pks

    return render(request, 'scenariohelp/configure_help.html', {
        'scenarios': scenarios,
        'active_nav': 'account'
    })


@require_POST
@login_required
def set_support(request):
    scenario_key = request.POST.get('scenario', '')
    scenario = get_object_or_404(Scenario, key=scenario_key, enabled=True)
    enabled = request.POST.get('enabled') == '1'

    if enabled:
        SupportedScenario.objects.get_or_create(user=request.user, scenario=scenario)
    else:
        SupportedScenario.objects.filter(user=request.user, scenario=scenario).delete()
    return HttpResponse('{"result": "ok"}', content_type='application/json')


@require_POST
@login_required
def set_support_scenario(request, scenario_pk):
    scenario = get_object_or_404(Scenario, pk=scenario_pk, enabled=True)

    SupportedScenario.objects.get_or_create(user=request.user, scenario=scenario)
    messages.success(request, _('Thank you for helping!'))
    return redirect('scenarios:view', scenario.key)


def _annotate_is_seen(question_list, user):
    seen_questions = SeenQuestion.objects.filter(user=user,
                                                 question__in=question_list)
    seen_pks = set(hq.question.pk for hq in seen_questions)
    for question in question_list:
        question.is_seen = question.pk in seen_pks or question.author == user

    return question_list
