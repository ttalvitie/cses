from django.http import HttpResponse
from django.shortcuts import render, redirect
from django import forms
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

class LoginForm(forms.Form):
	username = forms.CharField()
	password = forms.CharField(widget=forms.PasswordInput)

def login(request):
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			user = auth.authenticate(username=username, password=password)
			if user is not None and user.is_active:
				auth.login(request, user)
				return redirect('cses.views.index')
	else:
		form = LoginForm()
	return render(request, "login.html", {'form': form})

def index(request):
	if not request.user.is_authenticated():
		return redirect('cses.views.login')
	return HttpResponse("Index")