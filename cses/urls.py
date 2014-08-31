from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
	url(r'^$', views.index, name="cses-index"),
	url(r'^login/', views.login, name="cses-login"),
	url(r'^logout/', views.logout, name="cses-logout"),
	url(r'^register/', views.register, name="cses-register"),
	url(r'^contest/([0-9]+)/$', views.contest, name="cses-contest"),
	url(r'^submissions/([0-9]+)/$', views.submissions, name="cses-submissions"),
	url(r'^scoreboard/([0-9]+)/$', views.scoreboard, name="cses-scoreboard"),
	url(r'^viewsubmission/([0-9]+)/$', views.viewSubmission, name="cses-viewSubmission"),
	url(r'^import/', views.taskImport, name="cses-taskImport"),
	url(r'^rejudge/', views.rejudge, name="cses-rejudge"),
)
