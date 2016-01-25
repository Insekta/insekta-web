from django.contrib import admin
from django.utils.safestring import mark_safe

from insekta.scenarios.models import (Scenario, ScenarioGroup, ScenarioGroupEntry,
                                      Task, CommentId, Comment, Course)


class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('key', 'title', 'is_challenge', 'enabled', 'num_tasks')
    ordering = ('title', )


class ScenarioGroupEntryInline(admin.TabularInline):
    model = ScenarioGroupEntry
    ordering = ('order_id', )


class ScenarioGroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'frontpage', 'hidden', 'order_id', 'internal_comment')
    inlines = (ScenarioGroupEntryInline, )


class TaskAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'scenario', 'num_solved')
    list_filter = ('scenario__title', )
    filter_horizontal = ('solved_by', )

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


class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'enabled')
    filter_horizontal = ('scenario_groups', )


admin.site.register(Scenario, ScenarioAdmin)
admin.site.register(ScenarioGroup, ScenarioGroupAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(CommentId, CommentIdAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Course, CourseAdmin)
