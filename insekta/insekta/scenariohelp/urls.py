from django.urls import path

from insekta.scenariohelp import views


app_name = 'scenariohelp'
urlpatterns = [
    path('', views.list_questions, name='index'),
    path('view/<int:question_pk>', views.view_question, name='view'),
    path('my_questions', views.my_questions, name='my_questions'),
    path('scenario_questions/<course_key>/<scenario_key>', views.scenario_questions,
        name='scenario_questions'),
    path('new_question/<course_key>/<scenario_key>', views.new_question, name='new_question'),
    path('configure', views.configure_help, name='configure_help'),
    path('set_support_scenario/<course_key>/<scenario_key>', views.set_support_scenario,
        name='set_support_scenario'),
]
