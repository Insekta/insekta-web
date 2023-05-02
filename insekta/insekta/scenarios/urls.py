from django.urls import path

from insekta.scenarios import views


app_name = 'scenarios'
urlpatterns = [
    path('topiclist', views.index, name='index'),
    path('challenges', views.index, kwargs={
        'is_challenge': True
    }, name='challenges'),
    path('view/<course_key>/<scenario_key>', views.view, name='view'),
    path('download/<course_key>/<scenario_key>/<download_key>/<filename>',
         views.download, name='download'),
    path('vms/enable/<course_key>/<scenario_key>', views.enable_vms, name='enable_vms'),
    path('vms/disable/<course_key>/<scenario_key>', views.disable_vms, name='disable_vms'),
    path('vms/ping/<scenario_key>', views.ping_vms, name='ping_vms'),
    path('save_notes/<scenario_key>', views.save_notes, name='save_notes'),
    path('save_comments_state', views.save_comments_state, name='save_comments_state'),
    path('get_comments/<scenario_key>', views.get_comments, name='get_comments'),
    path('preview_comment', views.preview_comment, name='preview_comment'),
    path('save_comment/<scenario_key>', views.save_comment, name='save_comment'),
    path('courses/', views.list_courses, name='list_courses'),
    path('courses/<course_key>/topiclist', views.view_course, name='view_course'),
    path('courses/<course_key>/challenges', views.view_course, kwargs={
        'is_challenge': True
    }, name='view_course_challenges'),
    path('courses/<course_key>/registration', views.course_registration,
        name='course_registration'),
    path('courseruns/<course_run_pk>/allpoints', views.courserun_points,
        name='courserun_points'),
    path('courseruns/<course_run_pk>/points', views.courserun_points_participant,
        name='courserun_points_participant'),
    path('options/<course_key>/<scenario_key>', views.show_options, name='show_options'),
    path('reset_tasks/<course_key>/<scenario_key>', views.reset_tasks, name='reset_tasks'),
]
