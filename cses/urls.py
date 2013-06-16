from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
	url(r'^$', views.index),
	url(r'^login/', views.login),
	url(r'^logout/', views.logout),
	url(r'^contest/([0-9]+)/$', views.contest),
	url(r'^submissions/([0-9]+)/$', views.submissions),
	url(r'^scoreboard/([0-9]+)/$', views.scoreboard),
	url(r'^viewsubmission/([0-9]+)/$', views.viewSubmission),
	url(r'^import/', views.taskImport),
)
