from django.http import HttpResponse
from django.shortcuts import render, redirect
from django import forms
from django.contrib import auth
from django.core.urlresolvers import reverse

from utils import *
from django.conf import settings
import judging

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

def logout(request):
	if request.method == 'POST':
		auth.logout(request)
	
	return redirect('cses.views.login')

@require_login
def index(request):
	contests = getUserContests(request.user)
	
	return render(request, "index.html", {'contests': contests})

	
class ContestSubmitForm(forms.Form):
	task = forms.ModelChoiceField(queryset=Task.objects.none(), required=True)
	file = forms.FileField()
	language = forms.ModelChoiceField(queryset=Language.objects.all(), required=True)
	
	def __init__(self, contest, *args, **kwargs):
		super(ContestSubmitForm, self).__init__(*args, **kwargs)
		self.fields['task'].queryset = contest.tasks.all()

@contest_page
def contest(request, contest):
	if request.method == 'POST':
		form = ContestSubmitForm(contest, request.POST, request.FILES)
		if(form.is_valid() and form.cleaned_data['file']._size <= settings.CSES_MAX_SUBMISSION_SIZE):
			# TODO: error reporting
			submission = Submission(
				task=form.cleaned_data['task'],
				source=form.cleaned_data['file'],
				language=form.cleaned_data['language'],
				contest=contest,
				user=request.user
			)
			submission.save()
			judging.master.addSubmission(submission)

	else:
		form = ContestSubmitForm(contest)
	
	return render(request, "contest.html", {'contest': contest, 'form': form})
