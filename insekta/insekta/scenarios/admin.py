from django.contrib import admin
from django.utils.safestring import mark_safe

from insekta.scenarios.models import (Scenario, ScenarioGroup, ScenarioGroupEntry,
                                      Task, CommentId, Comment, Course, CourseRun,
                                      TaskConfiguration, TaskGroup, TaskSolve,
                                      TaskSolveArchive)


class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('key', 'title', 'is_challenge', 'enabled', 'num_tasks')
    ordering = ('title', )


class ScenarioGroupEntryInline(admin.TabularInline):
    model = ScenarioGroupEntry
    ordering = ('order_id', )


class ScenarioGroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'hidden', 'order_id', 'internal_comment')
    list_filter = ['course__short_name']
    orderering = ('course__title', 'title')
    inlines = (ScenarioGroupEntryInline, )


class TaskAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'scenario', 'order_id', 'num_solved')
    list_filter = ('scenario__title', )
    filter_horizontal = ('solved_by', )
    ordering = ('-scenario__pk', '-order_id')

    def num_solved(self, obj):
        return obj.solved_by.count()


class CommentInline(admin.TabularInline):
    model = Comment
    ordering = ('-time_created', )


class CommentIdAdmin(admin.ModelAdmin):
    list_display = ('comment_id', 'scenario', 'orphaned', 'num_comments')
    inlines = (CommentInline, )
    list_filter = ('scenario__title', 'orphaned')

    def num_comments(self, obj):
        count = obj.comments.all().count()
        if count == 0:
            return mark_safe('<span style="color:#ccc;">0</span>')
        return count


class CommentAdmin(admin.ModelAdmin):
    list_display = ('time_created', 'author', 'scenario', 'comment_id', 'text')
    list_filter = ('comment_id__scenario__title', )

    def scenario(self, obj):
        return obj.comment_id.scenario.title

    def comment_id(self, obj):
        return obj.comment_id.comment_id

    def text(self, obj):
        return obj.text[:160] + ('...' if len(obj.text) > 160 else '')


class ScenarioGroupInline(admin.TabularInline):
    model = ScenarioGroup
    ordering = ('order_id', )
    fields = ('title', 'hidden', 'order_id')
    readonly_fields = ('title', )
    extra = 0

    def has_add_permission(self, request):
        return False


class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'enabled')
    inlines = [ScenarioGroupInline]


class CourseRunAdmin(admin.ModelAdmin):
    list_display = ('course', 'name', 'enabled')


class TaskConfigurationAdmin(admin.ModelAdmin):
    list_display = ('task', )


class TaskConfigurationInline(admin.TabularInline):
    model = TaskConfiguration


class TaskGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'course_run', 'deadline_at')
    inlines = [TaskConfigurationInline]


class TaskSolveAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'is_correct')


class TaskSolveArchiveAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'course_run', 'is_correct')


admin.site.register(Scenario, ScenarioAdmin)
admin.site.register(ScenarioGroup, ScenarioGroupAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(CommentId, CommentIdAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseRun, CourseRunAdmin)
admin.site.register(TaskConfiguration, TaskConfigurationAdmin)
admin.site.register(TaskGroup, TaskGroupAdmin)
admin.site.register(TaskSolve, TaskSolveAdmin)
admin.site.register(TaskSolveArchive, TaskSolveArchiveAdmin)
