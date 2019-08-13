import json
from collections import defaultdict

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token
from django.conf import settings
from django.views.decorators.http import require_POST
from jinja2 import TemplateSyntaxError
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from insekta.base.utils import describe_allowed_markup, sanitize_markup
from insekta.remoteapi.client import remote_api
from insekta.scenarios.dsl.renderer import Renderer
from insekta.scenarios.dsl.taskparser import ParserError
from insekta.scenarios.dsl.tasks import TemplateTaskError
from insekta.scenarios.models import (Scenario, ScenarioGroup, Notes,
                                      CommentId, Comment, Course, CourseRun, TaskSolve, ScenarioError, TaskSolveArchive,
                                      TaskGroup, Task, TaskConfiguration)


COMPONENT_STYLESHEETS = {
}
COMPONENT_SCRIPTS = {
}


@login_required
def index(request):
    return redirect('scenarios:list_courses')


@login_required
def view(request, course_key, scenario_key):
    try:
        return _view_scenario(request, course_key, scenario_key)
    except (TemplateSyntaxError, ParserError) as e:
        if not request.user.is_superuser:
            raise
        scenario = Scenario.objects.get(key=scenario_key)
        with open(scenario.get_template_filename()) as f:
            template_source = f.read()
        lexer = get_lexer_by_name('jinja')
        formatter = HtmlFormatter(linenos=True, hl_lines=[e.lineno])
        template_html = mark_safe(highlight(template_source, lexer, formatter))
        return render(request, 'scenarios/render_error.html', {
            'template_html': template_html,
            'error_class': e.__class__.__name__,
            'error_message': str(e),
            'error_lineno': e.lineno
        })
    except (ScenarioError, TemplateTaskError) as e:
        if not request.user.is_superuser:
            raise
        return render(request, 'scenarios/render_error.html', {
            'error_class': e.__class__.__name__,
            'error_message': str(e),
        })
    except:
        raise


def _view_scenario(request, course_key, scenario_key):
    scenario = _get_scenario(scenario_key, request.user)
    course = get_object_or_404(Course, key=course_key)
    if not scenario.is_inside_course(course):
        raise Http404('Scenario is not contained in this course.')

    if _has_to_register(course, request.user):
        return redirect('scenarios:course_registration', course.key)

    if scenario.show_ethics_reminder and not request.user.accepted_ethics:
        ethics_url = (reverse('ethics:view') + "?next=" +
                      reverse('scenarios:view', args=(course.key, scenario_key, )))
        return redirect(ethics_url)


    # Load additional stylesheets and scripts
    additional_stylesheets = []
    additional_scripts = []
    for component in scenario.get_required_components():
        for stylesheet in COMPONENT_STYLESHEETS.get(component, []):
            additional_stylesheets.append(settings.STATIC_URL + stylesheet)
        for script in COMPONENT_SCRIPTS.get(component, []):
            additional_scripts.append(settings.STATIC_URL + script)
    scenario_path = settings.MEDIA_URL + 'scenarios/'
    for stylesheet in scenario.get_css_files():
        additional_stylesheets.append(scenario_path + stylesheet)
    for script in scenario.get_javascript_files():
        additional_scripts.append(scenario_path + script)

    # Load vm resources
    virtual_machines = {}
    expire_time = None
    vpn_ip = None
    vms_running = False
    vm_resource = scenario.get_vm_resource()
    if vm_resource:
        resource_status = remote_api.get_vm_resource_status(vm_resource, request.user)
        if resource_status['status'] == 'running':
            vms_running = True
            resource = resource_status['resource']
            virtual_machines = resource['virtual_machines']
            expire_time = resource['expire_time']
        vpn_ip = resource_status['vpn_ip']

    # Initialize renderer and submit request to it
    csrf_token = get_token(request)
    renderer = Renderer(course, scenario, request.user, csrf_token, virtual_machines, vpn_ip)
    if request.method == 'POST':
        submit_result = renderer.submit(request.POST)
        if submit_result.is_correct:
            scenario.solve(request.user, submit_result.task, submit_result.answer)

    try:
        notes = Notes.objects.get(user=request.user, scenario=scenario).content
    except Notes.DoesNotExist:
        notes = ''

    comments_enabled = json.dumps(request.session.get('comments_enabled', True))
    num_user_comments = json.dumps(scenario.get_comment_counts())

    return render(request, 'scenarios/view.html', {
        'course': course,
        'scenario': scenario,
        'rendered_scenario': renderer.render(),
        'additional_stylesheets': additional_stylesheets,
        'additional_scripts': additional_scripts,
        'has_vms': vm_resource is not None,
        'vms_running': vms_running,
        'vms': virtual_machines,
        'vms_expire_time': expire_time,
        'vpn_running': vpn_ip is not None,
        'vpn_ip': vpn_ip,
        'notes': notes,
        'comments_enabled': comments_enabled,
        'num_user_comments': num_user_comments,
        'has_solved_all': scenario.has_solved_all(request.user),
        'is_supporting': scenario.is_supported_by(request.user),
    })


def download(request, course_key, scenario_key, download_key, filename):
    scenario = _get_scenario(scenario_key, request.user)
    return HttpResponse(scenario.get_download(download_key),
                        content_type='application/x-octet-stream')


@require_POST
@login_required
def enable_vms(request, course_key, scenario_key):
    course = get_object_or_404(Course, key=course_key)
    if _has_to_register(course, request.user):
        return redirect('scenarios:course_registration', course.key)
    vm_resource = _get_scenario(scenario_key, request.user).get_vm_resource()
    if vm_resource:
        remote_api.start_vm_resource(vm_resource, request.user)
    return redirect('scenarios:view', course.key, scenario_key)


@require_POST
@login_required
def disable_vms(request, course_key, scenario_key):
    course = get_object_or_404(Course, key=course_key)
    if _has_to_register(course, request.user):
        return redirect('scenarios:course_registration', course.key)
    vm_resource = _get_scenario(scenario_key, request.user).get_vm_resource()
    if vm_resource:
        remote_api.stop_vm_resource(vm_resource, request.user)
    return redirect('scenarios:view', course.key, scenario_key)


@require_POST
@login_required
def ping_vms(request, scenario_key):
    vm_resource = _get_scenario(scenario_key, request.user).get_vm_resource()
    result = remote_api.ping_vm_resource(vm_resource, request.user)
    return render(request, 'scenarios/expire_time.html', {
        'expire_time': result['expire_time']
    })


@require_POST
@login_required
def save_notes(request, scenario_key):
    scenario = _get_scenario(scenario_key, request.user)
    notes, created = Notes.objects.get_or_create(user=request.user, scenario=scenario)
    notes.content = request.POST.get('notes', '')
    notes.save()
    return HttpResponse('{"result": "ok"}', content_type='application/json')


@require_POST
@login_required
def save_comments_state(request):
    request.session['comments_enabled'] = request.POST.get('enabled') == '1'
    return HttpResponse('{"result": "ok"}', content_type='application/json')


@login_required
def get_comments(request, scenario_key):
    scenario = _get_scenario(scenario_key, request.user)
    comment_id_str = request.GET.get('comment_id', '')
    comment_id = get_object_or_404(CommentId, scenario=scenario, comment_id=comment_id_str)
    return _get_comments_response(request, comment_id)


@require_POST
@login_required
def preview_comment(request):
    comment = request.POST.get('comment', '')
    comments_preview = sanitize_markup(comment)
    return HttpResponse(comments_preview)


@require_POST
@login_required
def save_comment(request, scenario_key):
    scenario = _get_scenario(scenario_key, request.user)
    comment_id_str = request.POST.get('comment_id', '')
    comment_id = get_object_or_404(CommentId, scenario=scenario, comment_id=comment_id_str)
    comment = request.POST.get('comment', '')
    if comment.strip() != '':
        comments_html = sanitize_markup(comment)
        Comment.objects.create(comment_id=comment_id,
                               author=request.user,
                               text=comments_html)

    return _get_comments_response(request, comment_id)


@login_required
def list_courses(request):
    return render(request, 'scenarios/list_courses.html', {
        'courses': Course.objects.filter(enabled=True).order_by('title'),
        'active_nav': 'courses'
    })


@login_required
def view_course(request, course_key, is_challenge=False):
    course = get_object_or_404(Course, key=course_key, enabled=True)
    if _has_to_register(course, request.user):
        return redirect('scenarios:course_registration', course.key)
    scenario_groups = list(course.scenario_groups.filter(hidden=False).order_by('order_id'))
    scenario_groups = ScenarioGroup.annotate_list(scenario_groups,
                                                  is_challenge=is_challenge,
                                                  user=request.user)
    return render(request, 'scenarios/view_course.html', {
        'course': course,
        'scenario_groups': scenario_groups,
        'is_challenge': is_challenge,
        'active_nav': 'challenges' if is_challenge else 'topics'
    })


@login_required
def show_options(request, course_key, scenario_key):
    course = get_object_or_404(Course, key=course_key)
    if _has_to_register(course, request.user):
        return redirect('scenarios:course_registration', course.key)
    scenario = _get_scenario(scenario_key, request.user)
    return render(request, 'scenarios/show_options.html', {
        'course': course,
        'scenario': scenario
    })


@login_required
@require_POST
def reset_tasks(request, course_key, scenario_key):
    course = get_object_or_404(Course, key=course_key)
    if _has_to_register(course, request.user):
        return redirect('scenarios:course_registration', course.key)
    scenario = _get_scenario(scenario_key, request.user)
    TaskSolve.objects.filter(user=request.user, task__scenario=scenario).delete()
    messages.success(request, _('The exercises were reset. You can now solve them again.'))
    return redirect('scenarios:show_options', course_key, scenario.key)


@login_required
def course_registration(request, course_key):
    course = get_object_or_404(Course, key=course_key)
    try:
        current_run = course.current_run
    except CourseRun.DoesNotExist:
        current_run = None
    if request.method == 'POST' and current_run:
        current_run.participants.add(request.user)
        return redirect('scenarios:view_course', course.key)
    return render(request, 'scenarios/course_registration.html', {
        'course': course,
        'current_run': current_run
    })


def participant_points(request):
    pass


@login_required
def courserun_points(request, course_run_pk):
    if not request.user.is_superuser:
        raise PermissionDenied('Not allowed.')
    return _courserun_points_table(request, course_run_pk)


@login_required
def courserun_points_participant(request, course_run_pk):
    return _courserun_points_table(request, course_run_pk, request.user)

def _courserun_points_table(request, course_run_pk, participant=None):
    course_run = get_object_or_404(CourseRun, pk=course_run_pk)
    prefetch = Prefetch('tasks', Task.objects.order_by('order_id'))
    task_groups = list(TaskGroup.objects.filter(course_run=course_run)
                                        .order_by('name')
                                        .prefetch_related(prefetch))
    participants = course_run.participants.all()
    if participant:
        participants = participants.filter(pk=participant.pk)
    participants = list(participants)
    archived_tasks = TaskSolveArchive.objects.filter(course_run=course_run)
    solve_lookup = defaultdict(set)
    for archived_task in archived_tasks:
        solve_lookup[archived_task.user_id].add(archived_task.task_id)

    task_points = {}
    for task_config in TaskConfiguration.objects.filter(task_group__in=task_groups):
        task_points[task_config.task_id] = task_config.points

    participant_results = {}
    max_tasks_points = 0
    max_total_points = 0
    for task_group in task_groups:
        max_total_points += task_group.total_points
        for task in task_group.tasks.order_by('order_id'):
            max_tasks_points += task_points[task.pk]
        for participant in participants:
            results = participant_results.setdefault(participant.pk, {
                'task_groups': [],
                'total_points': 0,
            })
            group = {
                'points': 0,
                'solved_tasks': []
            }
            max_group_points = 0
            for task in task_group.tasks.order_by('order_id'):
                points = task_points[task.pk]
                max_group_points += points
                is_solved = task.pk in solve_lookup[participant.pk]
                group['solved_tasks'].append(is_solved)
                if is_solved:
                    group['points'] += points
            results['total_points'] += group['points']
            group['points'] = group['points'] / max_group_points * task_group.total_points
            results['task_groups'].append(group)
    for participant in participants:
        results = participant_results[participant.pk]
        results['total_points'] /= max_tasks_points
        results['total_points'] *= max_total_points
        results['name'] = participant.get_full_name()
        if not results['name']:
            results['name'] = participant.username
    points_table = list(participant_results.values())
    ordering = request.GET.get('ordering', 'name')
    if ordering == 'points':
        ordering_fn = lambda entry: -entry['total_points']
    else:
        ordering_fn = lambda entry: entry['name'].lower()
    points_table.sort(key=ordering_fn)
    return render(request, 'scenarios/courserun_points.html', {
        'points_table': points_table,
        'task_groups': task_groups,
        'course_run': course_run,
        'ordering': ordering,
        'simple': 'simple' in request.GET,
        'view_type': 'participant' if participant else 'total'
    })


def _get_comments_response(request, comment_id):
    comments = Comment.objects.filter(comment_id=comment_id).order_by('time_created')
    allowed_markup = describe_allowed_markup()
    return render(request, 'scenarios/get_comments.html', {
        'comments': comments,
        'allowed_markup': allowed_markup
    })


def _get_scenario(scenario_key, user):
    if settings.DEBUG:
        scenario = Scenario.update_or_create_from_key(scenario_key)
    else:
        scenario_filter = {'key': scenario_key, 'enabled': True}
        if user.is_superuser:
            del scenario_filter['enabled']
        scenario = get_object_or_404(Scenario, **scenario_filter)
    return scenario


def _has_to_register(course, user):
    return course.requires_registration and \
           not course.current_run.participants.filter(pk=user.pk).exists()