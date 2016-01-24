from django.contrib import admin

from insekta.scenarios.models import (Scenario, ScenarioGroup, ScenarioGroupEntry,
                                      Task, CommentId, Comment)


admin.site.register(Scenario)
admin.site.register(ScenarioGroup)
admin.site.register(ScenarioGroupEntry)
admin.site.register(Task)
admin.site.register(CommentId)
admin.site.register(Comment)
