import os
import tempfile

from django.test import TestCase
from django.contrib.auth import get_user_model
from jinja2 import Environment

from insekta.scenarios.dsl.taskparser import TaskParser
from insekta.scenarios.dsl.renderer import Renderer
from insekta.scenarios.models import Scenario


TEMPLATE = '''
{% call task(identifier='hello', type='multiple_choice') %}
Hello World!
{% call choice(name='cookies', correct=True) %}I like cookies{% endcall %}
{% call choice(name='nocookies', correct=False) %}I don't like cookies{% endcall %}
{% call choice(name='morecookies', correct=True) %}I want more cookies{% endcall %}
{% endcall %}


{% call task(identifier='world', type='question', strip=False, case_sensitive=False) %}

{{ answer(expected='42') }}

{% endcall %}
'''


class ParserTestCase(TestCase):
    def setUp(self):
        self.env = Environment()

    def test_question(self):
        ast = self.env.parse(TEMPLATE)
        p = TaskParser(ast)
        tasks = p.get_tasks()
        self.assertEqual(len(tasks), 2)

        multiple_choice = tasks['hello']
        question = tasks['world']

        self.assertEqual(multiple_choice.identifier, 'hello')
        self.assertEqual(multiple_choice.task_type, 'multiple_choice')
        choices = multiple_choice.choices
        self.assertEqual(choices['cookies'].name, 'cookies')
        self.assertEqual(choices['cookies'].correct, True)
        self.assertEqual(choices['nocookies'].name, 'nocookies')
        self.assertEqual(choices['nocookies'].correct, False)
        self.assertEqual(choices['morecookies'].name, 'morecookies')
        self.assertEqual(choices['morecookies'].correct, True)

        self.assertEqual(question.identifier, 'world')
        self.assertEqual(question.task_type, 'question')
        self.assertEqual(question.answers, ['42'])
        self.assertEqual(question.strip, False)
        self.assertEqual(question.case_sensitive, False)


class RendererTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(username='test')
        self.scenario = Scenario.objects.create(key='test', title='Test', num_tasks=2)

    def test_renderer(self):
        with tempfile.TemporaryDirectory() as scenario_dir:
            os.makedirs(os.path.join(scenario_dir, 'test'))
            with open(os.path.join(scenario_dir, 'test', 'scenario.html'), 'w') as f:
                f.write(TEMPLATE)
            with self.settings(SCENARIO_DIR=scenario_dir):
                self._run_test_renderer()

    def _run_test_renderer(self):
        renderer = Renderer(self.scenario, self.user, 'somecsrftoken')
        hello = renderer.template_tasks['hello']
        cookies_key = hello.choices['cookies'].get_mac(
            self.user, self.scenario, hello.identifier)
        morecookies_key = hello.choices['morecookies'].get_mac(
            self.user, self.scenario, hello.identifier)
        tpl_task = renderer.submit({
            'task': hello.get_mac(self.user, self.scenario),
            cookies_key: '1',
            morecookies_key: '1'
        })
        self.assertEqual(tpl_task.identifier, hello.identifier)
        renderer.render()
