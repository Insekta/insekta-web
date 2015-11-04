import json
import os

from django.db import models
from django.conf import settings

from .dsl.taskparser import TaskParser


class ScenarioError(Exception):
    pass


class Scenario(models.Model):
    key = models.CharField(max_length=120, unique=True)
    title = models.CharField(max_length=255)
    challenge = models.BooleanField(default=False)
    num_tasks = models.IntegerField()
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def get_required_components(self):
        self._load_extra()
        return self._extra.get('required_components', [])

    def get_javascript_files(self):
        return self._get_static_files('js')

    def get_css_files(self):
        return self._get_static_files('css')

    def get_scenario_dir(self):
        return os.path.join(settings.SCENARIO_DIR, self.key)

    def get_template_filename(self):
        return os.path.join(self.get_scenario_dir(), 'scenario.html')

    def get_template_tasks(self):
        return TaskParser.from_filename(self.get_template_filename()).get_tasks()

    def update_tasks(self, purge=False):
        existing_tasks = {}
        for task in Task.objects.filter(scenario=self):
            existing_tasks[task.identifier] = task
        unused_task_identifiers = set(existing_tasks.keys())
        template_tasks = self.get_template_tasks()
        for tpl_task in template_tasks.values():
            unused_task_identifiers.discard(tpl_task.identifier)
            if tpl_task.identifier not in existing_tasks:
                Task.objects.create(scenario=self, identifier=tpl_task.identifier)
        self.num_tasks = len(template_tasks)
        self.save()

        if purge:
            for unused_task_identifier in unused_task_identifiers:
                existing_tasks[unused_task_identifier].delete()

    def solve(self, user, task_identifier):
        Task.objects.get(scenario=self, identifier=task_identifier).solved_by.add(user)

    def get_absolute_url(self):
        # FIXME
        return '/scenarios/view/{}'.format(self.key)

    def _load_extra(self):
        if hasattr(self, '_extra'):
            return
        try:
            with open(os.path.join(self.get_scenario_dir(), 'meta.json')) as f:
                extra = json.load(f)
        except (IOError, ValueError):
            raise ScenarioError('Could not load meta.json')
        self._extra = extra

    def _get_static_files(self, static_type):
        self._load_extra()
        static_files = []
        if 'static' not in self._extra or static_type not in self._extra['static']:
            return static_files
        for static_file in self._extra['static'][static_type]:
            if isinstance(static_file, list):
                scenario_key = static_file[0]
                filename = static_file[1]
            else:
                scenario_key = self.key
                filename = static_file
            static_files.append(os.path.join(scenario_key, 'static', filename))
        return static_files


class Task(models.Model):
    scenario = models.ForeignKey(Scenario, related_name='tasks')
    identifier = models.CharField(max_length=120)
    solved_by = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
                                       related_name='solved_tasks')

    def __str__(self):
        return '{} ({})'.format(self.identifier, self.scenario)


class ScenarioGroup(models.Model):
    title = models.CharField(max_length=255)
    scenarios = models.ManyToManyField(Scenario, related_name='groups')

    def __str__(self):
        return self.title
