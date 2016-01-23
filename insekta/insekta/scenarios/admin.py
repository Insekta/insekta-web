from django.contrib import admin

from insekta.scenarios.models import Scenario, ScenarioGroup, Task, CommentId, Comment


admin.site.register(Scenario)
admin.site.register(ScenarioGroup)
admin.site.register(Task)
admin.site.register(CommentId)
admin.site.register(Comment)