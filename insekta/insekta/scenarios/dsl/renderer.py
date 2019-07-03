import functools
import hmac
import io
import os
from collections import namedtuple

from django.conf import settings
from django.utils import html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from jinja2 import Environment, escape
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from insekta.scenarios.dsl.scripts import ScriptInputValidationError
from insekta.scenarios.dsl.templateloader import ScenarioTemplateLoader
from insekta.scenarios.models import Task, TaskSolve


__all__ = ['Renderer']


SubmitResult = namedtuple('SubmitResult', ['is_correct', 'task', 'answer'])


def collect_to_str(fn):
    def _wrap(*args, **kwargs):
        buf = io.StringIO()
        for token in fn(*args, **kwargs):
            buf.write(token)
        return buf.getvalue()

    return functools.update_wrapper(_wrap, fn)


class Renderer:
    def __init__(self, course, scenario, user, csrf_token, virtual_machines, vpn_ip):
        self.course = course
        self.scenario = scenario
        self.user = user
        self.csrf_token = csrf_token
        self.virtual_machines = virtual_machines
        self.vpn_ip = vpn_ip
        self.template_tasks = scenario.get_template_tasks()

        self.env = Environment(loader=_template_loader)
        for fn_name, fn in self._get_template_functions().items():
            self.env.globals[fn_name] = fn

        self._solved_task_answers = {}
        tasks = Task.objects.filter(scenario=scenario)
        solves = TaskSolve.objects.filter(user=user, task__in=tasks).select_related('task')
        for task_solve in solves:
            self._solved_task_answers[task_solve.task.identifier] = task_solve.answer

        self.submitted_values = {}
        self.submitted_task = None
        self.submitted_valid = False
        self.validation_error_message = None
        self.validation_context = {}
        self._current_task_identifier = ''

    @collect_to_str
    def _call_task(self, identifier, title=None, caller=None, **kwargs):
        self._current_task_identifier = identifier
        is_solved = self._task_is_solved()
        task_mac = self.template_tasks[identifier].get_mac(self.user, self.scenario)

        panel_type = 'success text-white' if is_solved else 'light'
        yield '<div id="task_{}"></div>'.format(task_mac)
        yield '<div class="card mb-3">\n'
        yield '<div class="card-header bg-{}">\n'.format(panel_type)
        if title:
            panel_title = _('Exercise: {}').format(title)
        else:
            panel_title = _('Exercise')
        yield '{}\n'.format(escape(panel_title))
        yield '</div>\n'
        yield '<div class="card-body">\n'

        if self._is_submitted_task():
            if self.submitted_valid:
                msg = _('Your answer is correct.')
                yield '<div class="alert alert-success">{}</div>\n'.format(msg)
            else:
                if self.validation_error_message:
                    error_msg = html.escape(self.validation_error_message)
                    msg = _('Unfortunately, our answer is incorrect: '
                            '<strong>{}</strong>').format(error_msg)
                else:
                    msg = _('Unfortunately, your answer is incorrect.')
                yield '<div class="alert alert-danger">{}</div>\n'.format(msg)

        form_action = '{}#task_{}'.format(self.scenario.get_absolute_url(self.course), task_mac)
        yield '<form method="post" action="{}">\n'.format(form_action)
        yield '<input type="hidden" name="csrfmiddlewaretoken" value="{}">\n'.format(
            self.csrf_token)
        yield '<input type="hidden" name="task" value="{}">\n'.format(task_mac)
        yield caller()
        if not is_solved:
            yield '<p><button class="btn btn-primary">{}</button></p>\n'.format(
                _('Solve exercise'))
        yield '</form>\n'
        yield '</div>\n'
        yield '</div>\n'
        self._current_task_identifier = ''

    @collect_to_str
    def _call_require_task(self, caller, identifier, **kwargs):
        if identifier in self._solved_task_answers:
            yield caller()
        else:
            msg = _('<strong>Here be dragons.</strong> '
                    'You have to solve an exercise to uncover more content.')
            yield '<div class="alert alert-info herebedragons">{}</div>\n'.format(msg)

    @collect_to_str
    def _call_choice(self, name, correct=False, caller=None, **kwargs):
        is_solved = self._task_is_solved()
        tpl_task = self._get_current_task()
        option_mac = tpl_task.choices[name].get_mac(self.user, self.scenario,
                                                    tpl_task.identifier)
        choice_type = 'radio' if tpl_task.task_type == 'single_choice' else 'checkbox'
        yield '<div class="form-check">\n'
        yield '<label>\n'
        extra = ''
        if is_solved:
            extra = ' disabled'
            if correct:
                extra += ' checked'
        else:
            add_check = (self._is_submitted_task() and
                         ((choice_type == 'checkbox' and self.submitted_values[name]) or
                          (choice_type == 'radio' and self.submitted_values['answer'] == name)))
            if add_check:
                extra += ' checked'
        if choice_type == 'radio':
            input_str = '<input type="radio" class="form-check-input" name="answer" value="{}"{}>'
        else:
            input_str = '<input type="checkbox" class="form-check-input" name="{}" value="1"{}>'
        yield input_str.format(option_mac, extra)
        yield caller()
        yield '</label>\n'
        yield '</div>\n'

    @collect_to_str
    def _call_answer(self, label=None, caller=None, **kwargs):
        task = self._get_current_task()
        task_mac = task.get_mac(self.user, self.scenario)
        yield '<div class="form-group">\n'
        if label is None:
            label = _('Your answer')
        if label != '':
            yield '<label for="answer_{}">{}</label>\n'.format(task_mac, escape(label))
        value = ''
        if self._is_submitted_task() and not self.submitted_valid:
            value = self.submitted_values['answer']
        elif self._task_is_solved():
            value = task.answers[0]
        extra = ''
        if self._task_is_solved():
            extra += ' disabled'
        yield ('<input type="text" class="form-control" name="answer" '
               'value="{}" id="answer_{}"{}>\n').format(value, task_mac, extra)
        yield '</div>'

    def _call_media(self, path):
        if isinstance(path, list):
            if len(path) != 2:
                raise ValueError('If path is a list, it must be [scenario_key, path]')
            scenario_key, path = path
        else:
            scenario_key = self.scenario.key
        return '{}scenarios/{}/static/{}'.format(settings.MEDIA_URL, scenario_key, path)

    def _call_code(self, language='text', linenos=True, linestart=1, lineend=None,
                   filename=None, caller=None):
        source_code = ''
        if caller:
            source_code = caller()
        elif filename is not None:
            scenario_dir = os.path.join(settings.SCENARIO_DIR, self.scenario.key)
            with open(os.path.join(scenario_dir, filename)) as f:
                lines = f.readlines()
            if lineend is None:
                lineend = len(lines)
            source_code = ''.join(lines[linestart - 1:lineend])

        lexer = get_lexer_by_name(language,
                                  stripall=True if caller else False,
                                  stripnl=False if filename else True)
        formatter = HtmlFormatter(linenos=linenos, linenostart=linestart)
        return highlight(source_code, lexer, formatter)

    @collect_to_str
    def _call_hint(self, caller):
        yield '<form class="hint-form">\n'
        yield '<button class="btn btn-sm btn-default hint-button">\n'
        yield ' <span class="hint-text">' + _('Show hint') + '</span>\n'
        yield '</button>\n'
        yield '<div class="alert alert-hint hint-content">\n'
        yield '<button class="hint-close close pull-right">&times;</button>\n'
        yield caller()
        yield '</div>\n'
        yield '</form>'

    def _call_vm_ip(self, vm_name, default=None):
        try:
            return self.virtual_machines[vm_name]['ip']
        except KeyError:
            return default if default is not None else '$IP'

    def _call_vm_enabled(self, vm_name):
        return vm_name in self.virtual_machines

    def _call_script_input(self, name, type='text', placeholder='', choices=None):
        task = self._get_current_task()
        try:
            answer = str(self._solved_task_answers[task.identifier][name])
            disabled = True
        except KeyError:
            disabled = False
            if self._is_submitted_task():
                answer = str(self.submitted_values.get(name, ''))
            else:
                answer = ''
        attrs = {'name': name, 'class': 'form-control'}
        if disabled:
            attrs['disabled'] = 'disabled'
        if type == 'longtext':
            attrs['rows'] = '5'
        elif type == 'select':
            pass
        else:
            attrs['type'] = type
            attrs['value'] = answer
            if placeholder:
                attrs['placeholder'] = placeholder
        attrs_str = ' '.join('{}="{}"'.format(key, escape(value))
                             for key, value in attrs.items())
        if type == 'longtext':
            return '<textarea {}>{}</textarea>'.format(attrs_str, escape(answer))
        elif type == 'select':
            options = []
            for choice_value, choice_text in choices:
                selected = 'selected="selected"' if answer == choice_value else ''
                options.append('<option value="{}"{}>{}</option>'.format(
                    escape(choice_value), selected, escape(choice_text)))
            return '<select {}>{}</select>'.format(attrs_str, '\n'.join(options))
        else:
            return '<input {}/>'.format(attrs_str)

    def _call_script_values(self):
        task = self._get_current_task()
        return task.get_values(self.user)

    def _call_validation_context(self):
        return self.validation_context

    def _task_is_solved(self):
        return self._current_task_identifier in self._solved_task_answers

    def _get_current_task(self):
        return self.template_tasks[self._current_task_identifier]

    def _is_submitted_task(self):
        return (self.submitted_task and
                self.submitted_task.identifier == self._current_task_identifier)

    def _get_template_functions(self):
        return {
            'task': self._call_task,
            'require_task': self._call_require_task,
            'choice': self._call_choice,
            'answer': self._call_answer,
            'media': self._call_media,
            'code': self._call_code,
            'hint': self._call_hint,
            'vm_ip': self._call_vm_ip,
            'vm_enabled': self._call_vm_enabled,
            'script_values': self._call_script_values,
            'script_input': self._call_script_input,
            'validation_context': self._call_validation_context,
        }

    def render(self, context=None):
        """Renders the scenario template.

        :param context: Dictionary with additional template values
        :return: str with the rendered template
        """
        if context is None:
            context = {}
        context.update({
            'submitted_values': self.submitted_values,
            'submitted_task': self.submitted_task,
            'submitted_valid': self.submitted_valid,
            'vms': self.virtual_machines,
            'vpn_ip': self.vpn_ip
        })
        return mark_safe(self.env.get_template(self.scenario.key).render(**context))

    def submit(self, form_values):
        """Submits a form for the given scenario and validates it.

        :param form_values: Dictionary with form values (e.g. POST data)
        :return: False no tasks validates, else TemplateTask object which validated
        """
        try:
            task_mac = form_values['task']
        except KeyError:
            return False

        for tpl_task in self.template_tasks.values():
            if hmac.compare_digest(tpl_task.get_mac(self.user, self.scenario), task_mac):
                self.submitted_values = tpl_task.extract_values(self.user,
                                                                self.scenario,
                                                                form_values)
                self.submitted_task = tpl_task
                try:
                    tpl_task.validate(self.submitted_values, self.validation_context)
                except ScriptInputValidationError as e:
                    self.validation_error_message = e.message
                else:
                    self.submitted_valid = True
                    self._solved_task_answers[tpl_task.identifier] = self.submitted_values
                    return SubmitResult(True, tpl_task, self.submitted_values)
        return SubmitResult(False, None, None)


_template_loader = ScenarioTemplateLoader(settings.SCENARIO_DIR)
