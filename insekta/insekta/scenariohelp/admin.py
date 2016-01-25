from django.contrib import admin

from insekta.scenariohelp.models import Question, Post, SeenQuestion, SupportedScenario


class PostInline(admin.TabularInline):
    model = Post


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('time_created', 'title', 'author', 'is_solved')
    ordering = ('-time_created', )
    list_filter = ('is_solved', 'author')
    inlines = (PostInline, )


class PostAdmin(admin.ModelAdmin):
    list_display = ('time_created', 'author', 'post')
    ordering = ('-time_created', )
    list_filter = ('author', )

    def post(self, obj):
        return obj.text[:160] + ('...' if len(obj.text) > 160 else '')


class SeenQuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'user')
    list_filter = ('user', )


class SupportedScenarioAdmin(admin.ModelAdmin):
    list_display = ('scenario', 'user')
    list_filter = ('scenario__title', 'user')


admin.site.register(Question, QuestionAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(SeenQuestion, SeenQuestionAdmin)
admin.site.register(SupportedScenario, SupportedScenarioAdmin)
