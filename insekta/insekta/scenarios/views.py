import os

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token
from django.conf import settings

from .dsl.renderer import Renderer
from .models import Scenario, ScenarioGroup, Task


COMPONENT_STYLESHEETS = {
    'katex': ['katex/katex.min.css']
}
COMPONENT_SCRIPTS = {
    'raphaeljs': ['raphael/raphael.min.js'],
    'katex': ['katex/katex.min.js']
}


@login_required
def index(request):
    scenario_groups = ScenarioGroup.objects.filter(
        scenarios__enabled=True, scenarios__challenge=False).prefetch_related()

    scenario_lookup = {}
    for scenario_group in scenario_groups:
        scenario_group.scenario_list = list(scenario_group.scenarios.all())
        for scenario in scenario_group.scenario_list:
            scenario.tasks_solved = 0
            scenario_lookup[scenario.pk] = scenario
    solved_tasks = Task.objects.filter(solved_by=request.user,
                                       scenario__pk__in=scenario_lookup.keys())
    for solved_task in solved_tasks:
        scenario_lookup[solved_task.scenario.pk].tasks_solved += 1

    return render(request, 'scenarios/index.html', {
        'scenario_groups': scenario_groups
    })


@login_required
def view(request, scenario_key):
    scenario_filter = {'key': scenario_key, 'enabled': True}
    if request.user.is_superuser:
        del scenario_filter['enabled']
    scenario = get_object_or_404(Scenario, **scenario_filter)

    csrf_token = get_token(request)
    renderer = Renderer(scenario, request.user, csrf_token)
    if request.method == 'POST':
        tpl_task = renderer.submit(request.POST)
        if tpl_task:
            scenario.solve(request.user, tpl_task.identifier)

    additional_stylesheets = []
    additional_scripts = []
    component_path = os.path.join(settings.STATIC_URL, 'components')
    for component in scenario.get_required_components():
        for stylesheet in COMPONENT_STYLESHEETS.get(component, []):
            stylesheet = os.path.join(component_path, stylesheet)
            additional_stylesheets.append(stylesheet)
        for script in COMPONENT_SCRIPTS.get(component, []):
            script = os.path.join(component_path, script)
            additional_scripts.append(script)
    scenario_path = settings.MEDIA_URL + 'scenarios/'
    for stylesheet in scenario.get_css_files():
        stylesheet = os.path.join(scenario_path, stylesheet)
        additional_stylesheets.append(stylesheet)
    for script in scenario.get_javascript_files():
        script = os.path.join(scenario_path, script)
        additional_scripts.append(script)

    return render(request, 'scenarios/view.html', {
        'scenario': scenario,
        'rendered_scenario': renderer.render(),
        'additional_stylesheets': additional_stylesheets,
        'additional_scripts': additional_scripts
    })
