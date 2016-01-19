import errno
import json
import os
import re
import shutil

from django.db import models
from django.conf import settings

from insekta.scenarios.dsl.taskparser import TaskParser


class ScenarioError(Exception):
    pass


class Scenario(models.Model):
    key = models.CharField(max_length=120, unique=True)
    title = models.CharField(max_length=255)
    is_challenge = models.BooleanField(default=False)
    num_tasks = models.IntegerField(default=0)
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    @property
    def show_ethics_reminder(self):
        self._load_extra()
        return self._extra.get('show_ethics_reminder', False)

    def get_vm_resource(self):
        self._load_extra()
        return self._extra.get('vm_resource')

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

    @classmethod
    def update_or_create_from_key(cls, key):
        if not re.match('^[a-z0-9][a-z0-9-]*$', key):
            raise ScenarioError('Invalid characters in key: {}'.format(key))
        try:
            with open(os.path.join(settings.SCENARIO_DIR, key, 'meta.json')) as f:
                meta = json.load(f)
        except IOError as e:
            raise ScenarioError("Can't open meta.json: {}".format(e))
        except ValueError as e:
            raise ScenarioError('meta.json contains syntax errors: {}'.format(e))

        if 'title' not in meta:
            raise ScenarioError('meta.json must specify a title.')

        title = meta['title']
        is_challenge = meta.get('is_challenge', False)
        requires_vpn = meta.get('requires_vpn', False)

        if not isinstance(title, str):
            raise ScenarioError('title must be of type str')
        if not isinstance(is_challenge, bool):
            raise ScenarioError('is_challenge must be of type str')

        # Copy scenario static files to media_root/scenario_key/static
        scenario_media = os.path.join(settings.MEDIA_ROOT, 'scenarios', key, 'static')
        scenario_static = os.path.join(settings.SCENARIO_DIR, key, 'static')
        if os.path.exists(scenario_static):
            shutil.rmtree(scenario_media, ignore_errors=True)
            shutil.copytree(scenario_static, scenario_media)

        scenario, _created = cls.objects.get_or_create(key=key)
        scenario.title = title
        scenario.is_challenge = is_challenge
        scenario.requires_vpn = requires_vpn
        scenario.update_tasks()
        scenario.save()
        return scenario


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


class Notes(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    scenario = models.ForeignKey(Scenario)
    content = models.TextField(blank=True)

    class Meta:
        unique_together = ('user', 'scenario')

    def __str__(self):
        return 'Notes for user {} at scenario {}'.format(self.user, self.scenario)
