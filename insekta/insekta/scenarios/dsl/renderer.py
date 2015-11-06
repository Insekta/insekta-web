import hmac
import io
import functools

from jinja2 import Environment, FileSystemLoader, escape
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.conf import settings
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


__all__ = ['Renderer']


def collect_to_str(fn):
    def _wrap(*args, **kwargs):
        buf = io.StringIO()
        for token in fn(*args, **kwargs):
            buf.write(token)
        return buf.getvalue()

    return functools.update_wrapper(_wrap, fn)


class Renderer:
    def __init__(self, scenario, user, csrf_token):
        self.scenario = scenario
        self.user = user
        self.csrf_token = csrf_token
        self.template_tasks = scenario.get_template_tasks()

        self.env = Environment(loader=FileSystemLoader(scenario.get_scenario_dir()))
        for fn_name, fn in self._get_template_functions().items():
            self.env.globals[fn_name] = fn

        self._solved_task_identifiers = set()
        for task in user.solved_tasks.filter(scenario=scenario):
            self._solved_task_identifiers.add(task.identifier)

        self.submitted_values = {}
        self.submitted_task = None
        self.submitted_valid = False
        self._current_task_identifier = ''

    @collect_to_str
    def _call_task(self, identifier, title=None, caller=None, **kwargs):
        self._current_task_identifier = identifier
        is_solved = self._task_is_solved()
        task_mac = self.template_tasks[identifier].get_mac(self.user, self.scenario)

        panel_type = 'success' if is_solved else 'default'
        yield '<div class="panel panel-{}" id="task_{}">\n'.format(panel_type, task_mac)
        yield '<div class="panel-heading">\n'
        if title:
            panel_title = _('Task: {}').format(title)
        else:
            panel_title = _('Exercise')
        yield '<h3 class="panel-title">{}</h3>\n'.format(escape(panel_title))
        yield '</div>\n'
        yield '<div class="panel-body">\n'

        if self._is_submitted_task():
            if self.submitted_valid:
                msg = _('Congratulation. Your answer is correct.')
                yield '<div class="alert alert-success">{}</div>\n'.format(msg)
            else:
                msg = _('Sorry, your answer is incorrect.')
                yield '<div class="alert alert-danger">{}</div>\n'.format(msg)

        form_action = '{}#task_{}'.format(self.scenario.get_absolute_url(), task_mac)
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
        if identifier in self._solved_task_identifiers:
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
        yield '<div class="{}">\n'.format(choice_type)
        yield '<label>\n'
        extra = ''
        if is_solved:
            extra = ' disabled'
            if correct:
                extra += ' checked'
        else:
            add_check =  (self._is_submitted_task() and
                          (choice_type == 'checkbox' and self.submitted_values[name]) or
                          (choice_type == 'radio' and self.submitted_values['answer'] == name))
            if add_check:
                extra += ' checked'
        if choice_type == 'radio':
            input_str = '<input type="radio" name="answer" value="{}"{}>'
        else:
            input_str = '<input type="checkbox" name="{}" value="1"{}>'
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

    def _call_code(self, language, linenos=True, caller=None):
        lexer = get_lexer_by_name(language, stripall=True)
        formatter = HtmlFormatter(linenos=linenos)
        if not caller:
            caller = lambda: 'ERROR: No source code given'
        return highlight(caller(), lexer, formatter)

    def _task_is_solved(self):
        return self._current_task_identifier in self._solved_task_identifiers

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
            'submitted_valid': self.submitted_valid
        })
        return mark_safe(self.env.get_template('scenario.html').render(**context))

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
                if tpl_task.validate(self.submitted_values):
                    self.submitted_valid = True
                    self._solved_task_identifiers.add(tpl_task.identifier)
                    return tpl_task
        return False
