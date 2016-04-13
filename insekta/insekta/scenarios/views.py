import json

import bleach
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token
from django.conf import settings
from django.views.decorators.http import require_POST

from insekta.base.utils import describe_allowed_markup
from insekta.remoteapi.client import remote_api
from insekta.scenarios.dsl.renderer import Renderer
from insekta.scenarios.models import Scenario, ScenarioGroup, Task, Notes, CommentId, Comment, Course


COMPONENT_STYLESHEETS = {
}
COMPONENT_SCRIPTS = {
    'raphaeljs': ['raphael/raphael.min.js'],
    'flot': ['flot/jquery.flot.min.js'],
    'flot-categories': ['flot/jquery.flot.categories.min.js']
}


@login_required
def index(request, is_challenge=False):
    if 'course' in request.session:
        name = 'scenarios:view_course'
        if is_challenge:
            name += '_challenges'
        return redirect(name, request.session['course']['pk'])
    else:
        return redirect('scenarios:list_courses')


@login_required
def view(request, scenario_key):
    scenario = _get_scenario(scenario_key, request.user)

    if scenario.show_ethics_reminder and not request.user.accepted_ethics:
        ethics_url = (reverse('ethics:view') + "?next=" +
                      reverse('scenarios:view', args=(scenario_key, )))
        return redirect(ethics_url)


    # Load additional stylesheets and scripts
    additional_stylesheets = []
    additional_scripts = []
    component_path = settings.STATIC_URL + 'components/'
    for component in scenario.get_required_components():
        for stylesheet in COMPONENT_STYLESHEETS.get(component, []):
            additional_stylesheets.append(component_path + stylesheet)
        for script in COMPONENT_SCRIPTS.get(component, []):
            additional_scripts.append(component_path + script)
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
    renderer = Renderer(scenario, request.user, csrf_token, virtual_machines, vpn_ip)
    if request.method == 'POST':
        tpl_task = renderer.submit(request.POST)
        if tpl_task:
            scenario.solve(request.user, tpl_task.identifier)

    try:
        notes = Notes.objects.get(user=request.user, scenario=scenario).content
    except Notes.DoesNotExist:
        notes = ''

    comments_enabled = json.dumps(request.session.get('comments_enabled', True))
    num_user_comments = json.dumps(scenario.get_comment_counts())

    return render(request, 'scenarios/view.html', {
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
        'num_user_comments': num_user_comments
    })


@require_POST
@login_required
def enable_vms(request, scenario_key):
    vm_resource = _get_scenario(scenario_key, request.user).get_vm_resource()
    if vm_resource:
        remote_api.start_vm_resource(vm_resource, request.user)
    return redirect('scenarios:view', scenario_key)


@require_POST
@login_required
def disable_vms(request, scenario_key):
    vm_resource = _get_scenario(scenario_key, request.user).get_vm_resource()
    if vm_resource:
        remote_api.stop_vm_resource(vm_resource, request.user)
    return redirect('scenarios:view', scenario_key)


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
    comments_preview = bleach.clean(bleach.linkify(comment),
                                    tags=settings.TAG_WHITELIST,
                                    attributes=settings.ATTR_WHITELIST)
    return HttpResponse(comments_preview)


@require_POST
@login_required
def save_comment(request, scenario_key):
    scenario = _get_scenario(scenario_key, request.user)
    comment_id_str = request.POST.get('comment_id', '')
    comment_id = get_object_or_404(CommentId, scenario=scenario, comment_id=comment_id_str)
    comment = request.POST.get('comment', '')
    if comment.strip() != '':
        comments_html = bleach.clean(bleach.linkify(comment),
                                     tags=settings.TAG_WHITELIST,
                                     attributes=settings.ATTR_WHITELIST)
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
def view_course(request, course_pk, is_challenge=False):
    course = get_object_or_404(Course, pk=course_pk, enabled=True)
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
@require_POST
def choose_course(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk, enabled=True)
    request.session['course'] = {
        'pk': course.pk,
        'short_name': course.short_name
    }
    return redirect('scenarios:index')


@login_required
def show_options(request, scenario_key):
    scenario = _get_scenario(scenario_key, request.user)
    return render(request, 'scenarios/show_options.html', {
        'scenario': scenario
    })


@login_required
@require_POST
def reset_tasks(request, scenario_key):
    scenario = _get_scenario(scenario_key, request.user)
    request.user.solved_tasks.filter(scenario=scenario).delete()
    messages.success(request, _('The exercises were reset. You can now solve them again.'))
    return redirect('scenarios:show_options', scenario.key)


def _get_comments_response(request, comment_id):
    comments = Comment.objects.filter(comment_id=comment_id).order_by('time_created')
    allowed_markup = describe_allowed_markup(settings.TAG_WHITELIST, settings.ATTR_WHITELIST)
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
