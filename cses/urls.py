from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
	url(r'^$', views.index),
	url(r'^login/', views.login),
	url(r'^logout/', views.logout),
	url(r'^contest/([0-9]+)/$', views.contest),
)
