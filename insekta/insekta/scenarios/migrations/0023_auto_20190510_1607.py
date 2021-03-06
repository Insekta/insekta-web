# Generated by Django 2.2.1 on 2019-05-10 14:07

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('scenarios', '0022_remove_task_solved_by_old'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseRun',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('enabled', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='TaskGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('deadline_at', models.DateTimeField()),
                ('total_points', models.IntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='course',
            name='requires_registration',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='tasksolve',
            name='is_correct',
            field=models.BooleanField(default=True),
        ),
        migrations.CreateModel(
            name='TaskConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points', models.IntegerField(default=0)),
                ('delay_solution', models.BooleanField(default=False)),
                ('course_run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scenarios.CourseRun')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scenarios.Task')),
                ('task_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scenarios.TaskGroup')),
            ],
        ),
        migrations.AddField(
            model_name='courserun',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scenarios.Course'),
        ),
        migrations.AddField(
            model_name='courserun',
            name='participants',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='TaskSolveArchive',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('is_correct', models.BooleanField(default=True)),
                ('course_run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scenarios.CourseRun')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scenarios.Task')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('task', 'user', 'course_run')},
            },
        ),
    ]
