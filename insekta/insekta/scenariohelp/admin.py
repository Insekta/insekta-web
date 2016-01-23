from django.contrib import admin

from insekta.scenariohelp.models import Question, Post, SeenQuestion, SupportedScenario


admin.site.register(Question)
admin.site.register(Post)
admin.site.register(SeenQuestion)
admin.site.register(SupportedScenario)
