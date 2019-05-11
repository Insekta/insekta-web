import json
import os
import re
import shutil
from collections import namedtuple

from django.contrib.postgres.fields import JSONField
from django.db import models, IntegrityError
from django.conf import settings
from django.db.models import Count
from django.db.models.signals import pre_save
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.urls import reverse

from insekta.scenarios.dsl.taskparser import TaskParser

_scenario_script_cache = {}

ScriptCacheEntry = namedtuple('ScriptCacheEntry', ['mtime', 'script_classes'])


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

    def get_scripts_filename(self):
        return os.path.join(self.get_scenario_dir(), 'scripts.py')

    def get_template_tasks(self):
        return TaskParser.from_filename(self.get_template_filename(), self).get_tasks()

    def get_script_classes(self):
        scripts_filename = self.get_scripts_filename()
        try:
            mtime = os.stat(scripts_filename).st_mtime
            script_cache = _scenario_script_cache.get(self.pk)
            if script_cache:
                if script_cache.mtime == mtime:
                    return script_cache.script_classes
            with open(scripts_filename) as f:
                mod = {}
                exec(f.read(), mod, mod)
                if 'script_classes' not in mod:
                    raise ValueError('{} is missing script_classes'.format(
                        scripts_filename
                    ))
                cache_entry = ScriptCacheEntry(mtime, mod['script_classes'])
                _scenario_script_cache[self.pk] = cache_entry
                return mod['script_classes']
        except IOError:
            return {}

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

    def update_comment_ids(self, purge=False):
        with open(self.get_template_filename()) as f:
            contents = f.read()
        comment_ids = set(re.findall(r'data-comment-id="([a-z0-9_-]{0,64})"', contents))

        orphaned = CommentId.objects.filter(scenario=self).exclude(comment_id__in=comment_ids)
        for orphaned_cid in orphaned:
            if orphaned_cid.get_num_usages() == 0:
                orphaned_cid.delete()
            else:
                if purge:
                    orphaned_cid.comments.all().delete()
                    orphaned_cid.delete()
                else:
                    orphaned_cid.orphaned = True
                    orphaned_cid.save()

        for comment_id in comment_ids:
            comment_id_obj, created = CommentId.objects.get_or_create(
                    scenario=self, comment_id=comment_id)
            if not created:
                comment_id_obj.orphaned = False
                comment_id_obj.save()

    def solve(self, user, task_obj, answer):
        task = Task.objects.get(scenario=self, identifier=task_obj.identifier)
        if not task_obj.must_remember_answer:
            answer = None

        try:
            TaskSolve.objects.create(task=task, user=user, answer=answer)
        except IntegrityError:
            pass

    def get_absolute_url(self, course):
        return reverse('scenarios:view', args=(course.key, self.key, ))

    def get_comment_counts(self):
        comment_ids = CommentId.objects.filter(scenario=self, orphaned=False).annotate(
            num_comments=models.Count('comments'))
        comment_counts = {}
        for comment_id in comment_ids:
            comment_counts[comment_id.comment_id] = comment_id.num_comments
        return comment_counts

    def has_solved_all(self, user):
        return self.tasks.count() == user.solved_tasks.filter(scenario=self).count()

    def is_supported_by(self, user):
        return bool(self.supportedscenario_set.filter(user=user).count())

    def is_inside_course(self, course):
        return self.groups.filter(course=course).count() > 0

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
        if not re.match('^[a-z0-9][a-z0-9-_]*$', key):
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
        scenario.update_comment_ids()
        scenario.save()
        return scenario


class Task(models.Model):
    scenario = models.ForeignKey(Scenario, related_name='tasks', on_delete=models.CASCADE)
    identifier = models.CharField(max_length=120)
    solved_by = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
                                       through='TaskSolve',
                                       related_name='solved_tasks')

    def __str__(self):
        return '{} ({})'.format(self.identifier, self.scenario)


class TaskSolve(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    answer = JSONField(blank=True, null=True)
    is_correct = models.BooleanField(default=True)

    class Meta:
        unique_together = (('task', 'user'),)


class Course(models.Model):
    title = models.CharField(max_length=120)
    short_name = models.CharField(max_length=15)
    key = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)
    enabled = models.BooleanField(default=False)
    requires_registration = models.BooleanField(default=False)

    @cached_property
    def current_run(self):
        return CourseRun.objects.get(course=self, enabled=True)

    def __str__(self):
        return self.title


class CourseRun(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    enabled = models.BooleanField(default=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                          blank=True)

    def __str__(self):
        return '{}: {}'.format(self.course, self.name)


class TaskSolveArchive(models.Model):
    course_run = models.ForeignKey(CourseRun, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    answer = JSONField(blank=True, null=True)
    is_correct = models.BooleanField(default=True)

    class Meta:
        unique_together = (('task', 'user', 'course_run'),)


class TaskGroup(models.Model):
    name = models.CharField(max_length=120)
    deadline_at = models.DateTimeField()
    total_points = models.IntegerField()
    course_run = models.ForeignKey(CourseRun, on_delete=models.CASCADE)
    tasks = models.ManyToManyField(Task, through='TaskConfiguration')

    def __str__(self):
        return self.name


class TaskConfiguration(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    task_group = models.ForeignKey('TaskGroup', on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    delay_solution = models.BooleanField(default=False)


class ScenarioGroup(models.Model):
    title = models.CharField(max_length=255)
    course = models.ForeignKey(Course, related_name='scenario_groups', on_delete=models.CASCADE)
    hidden = models.BooleanField(default=False)
    order_id = models.IntegerField(default=1)
    description = models.TextField(blank=True, null=True)
    internal_comment = models.TextField(blank=True, null=True)
    scenario_objects = models.ManyToManyField(Scenario,
                                              through='ScenarioGroupEntry',
                                              related_name='groups')

    @staticmethod
    def annotate_list(scenario_group_list, is_challenge=None, user=None):
        """Annotate a list of ScenarioGroup objects with scenarios attribute.

        After calling this function, the ScenarioGroup objects in the list
        will have an scenarios attribute, which is a sorted list of scenarios.
        Additionally those scenarios will have an attribute num_tasks_solved,
        which tells you, how many tasks were solved by the user.

        :param scenario_group_list: List of ScenarioGroup objects
        :param user: A django user
        :return: list of ScenarioGroup objects
        """
        assert isinstance(scenario_group_list, list)

        group_lookup = {group.pk: group for group in scenario_group_list}
        for group in scenario_group_list:
            group.scenarios = []

        all_entries = (ScenarioGroupEntry.objects.select_related('scenario')
                       .filter(scenario_group__in=scenario_group_list,
                               scenario__enabled=True)
                       .order_by('order_id'))
        scenario_lookup = {}
        for entry in all_entries:
            scenario = entry.scenario
            take_scenario = (is_challenge is None or
                             scenario.is_challenge == is_challenge)
            if not take_scenario:
                continue
            group = group_lookup[entry.scenario_group.pk]
            group.scenarios.append(scenario)
            scenario_lookup[scenario.pk] = scenario

        for scenario in scenario_lookup.values():
            scenario.num_tasks_solved = 0
        if user:
            task_counts = (Task.objects.filter(solved_by=user)
                           .values('scenario').annotate(num_solved=Count('id')))
            for task_count in task_counts:
                scenario_pk = task_count['scenario']
                if scenario_pk in scenario_lookup:
                    scenario = scenario_lookup[scenario_pk]
                    scenario.num_tasks_solved = task_count['num_solved']

        return [group for group in scenario_group_list if group.scenarios]

    def __str__(self):
        return self.title


class ScenarioGroupEntry(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    scenario_group = models.ForeignKey(ScenarioGroup, on_delete=models.CASCADE)
    order_id = models.IntegerField(default=1)

    def __str__(self):
        return '{}: {}'.format(self.scenario_group, self.scenario)


class Notes(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    content = models.TextField(blank=True)

    class Meta:
        unique_together = ('user', 'scenario')

    def __str__(self):
        return 'Notes for user {} at scenario {}'.format(self.user, self.scenario)


class CommentId(models.Model):
    comment_id = models.CharField(max_length=64)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    orphaned = models.BooleanField(default=False)

    class Meta:
        unique_together = ('scenario', 'comment_id')

    def __str__(self):
        return '{}: {}'.format(self.scenario, self.comment_id)

    def get_num_usages(self):
        return Comment.objects.filter(comment_id=self).count()


class Comment(models.Model):
    comment_id = models.ForeignKey(CommentId, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    time_created = models.DateTimeField(default=now)
    text = models.TextField()

    def __str__(self):
        return '{}: {} at {}'.format(self.comment_id, self.author, self.time_created)


def _copy_task_solve(sender, instance, **kwargs):
    user = instance.user
    scenario_groups = instance.task.scenario.groups.all()
    courses = Course.objects.filter(scenario_groups__in=scenario_groups)
    course_runs = CourseRun.objects.filter(enabled=True,
                                           course__in=courses,
                                           participants=user)
    for course_run in course_runs:

        try:
            task_group = TaskGroup.objects.get(
                taskconfiguration__task=instance.task, course_run=course_run)
        except TaskGroup.DoesNotExist:
            continue
        if task_group.deadline_at < now():
            continue
        archived_solve, created = TaskSolveArchive.objects.get_or_create(
            course_run=course_run, user=user, task=instance.task)
        archived_solve.answer = instance.answer
        archived_solve.is_correct = instance.is_correct
        archived_solve.save()


pre_save.connect(_copy_task_solve, sender=TaskSolve)