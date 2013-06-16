from django.http import HttpResponse
from django.shortcuts import render, redirect
from django import forms
from django.contrib import auth
from django.core.urlresolvers import reverse

from utils import *
from django.conf import settings
import judging
import result
from datetime import datetime
import models

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import guess_lexer_for_filename

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
	if request.method == 'GET':
		auth.logout(request)
	
	return redirect('cses.views.login')

@require_login
def index(request):
	contests = getUserContests(request.user)
	if len(contests) == 1:
		return redirect('contest/' + str(contests[0].id) + '/')
	else:
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
	now = datetime.now()
	if now > contest.endTime or now < contest.startTime:
		message = 'Contest has ended.' if now>contest.endTime else 'Contest has not started.'
		return render(request, "contestend.html", {'contest':contest, 'message':message})
	if request.method == 'POST':
		form = ContestSubmitForm(contest, request.POST, request.FILES)
		if(form.is_valid() and form.cleaned_data['file']._size <= settings.CSES_MAX_SUBMISSION_SIZE):
			print 'adding submission at time',datetime.now()
			# TODO: error reporting
			submission = Submission(
				task=form.cleaned_data['task'],
				source=form.cleaned_data['file'],
				language=form.cleaned_data['language'],
				contest=contest,
				user=request.user,
				judgeResult=result.Result.PENDING,
				time=datetime.now()
			)
			submission.save()
			judging.master.addSubmission(submission)

	else:
		form = ContestSubmitForm(contest)
	
	return render(request, "contest.html", {'contest': contest, 'form': form})

@contest_page
def submissions(request, contest):
	userSubs = Submission.objects.filter(user=request.user, contest=contest).order_by('-time')
	return render(request, 'submissions.html', {'submissions': userSubs, 'contest': contest})

def resultColor(res):
	if res>0:
		return '#00FF00'
	if result.notDone(res):
		return '#FFFF00'
	if res==0:
		return '#000000'
	return '#FF0000'

def submissionCell(submitData, contestType, showLinks):
	if submitData == None:
		return '<td></td>'
	(submission, _, count) = submitData
	time = submission.submitTime()
	res = submission.judgeResult
	content = ''
	if contestType==models.Contest.Type.ICPC:
		content = str(count)+'<br/>'+str(time)
	else:
		content = str(submission.points())+'<br/>'+str(time)
	if showLinks:
		url = reverse('cses.views.viewSubmission', args=(submission.id,))
		content = '<a href="%s">%s</a>' % (url, content)
	
	return '<td bgcolor="%s" width="%d" height="%d">%s</td>' % (resultColor(res), 40, 40, content)

def countResult(user, scores, contest):
	resTime = 0
	resPoints = 0
	for i in scores:
		if i == None:
			continue
		(submission, time, count) = i
#		res = submission.judgeResult
		score = submission.points()
		resPoints += score
		if score!=0:
			resTime += time
			resTime += submission.submitTime()
	return (-resPoints, resTime, user)

def makeScoreboard(contest, showLinks, user):
	submits = contest.latestSubmits()
	isIOI = contest.contestType==models.Contest.Type.IOI
	users = map(unicode, contest.users.all() if showLinks or not isIOI else [user])
	taskM = contest.tasks.all()
	tasks = map(unicode, taskM.order_by('name'))
	table = [[(submits[t][u] if t in submits and u in submits[t] else None) for t in tasks] for u in users]
	uresults = sorted([countResult(i, table[i], contest) for i in xrange(len(users))])

	res = '<table border="1">'
	res += '<tr><td>Rank</td><td>Team</td><td>Score</td><td>Time</td>'
#	for task in tasks:
#		res += '<td>'+task+'</td>'
	for i in xrange(len(tasks)):
		data = chr(ord('A')+i)
		if isIOI:
			data+=' '+str(taskM[i].score)
		res += '<td>'+data+'</td>'
	res += '</tr>'
	for i in xrange(len(table)):
		(score, time, uidx) = uresults[i]
		res += '<tr><td>'+str(1+i)+'</td><td>'+users[uidx]+'</td><td>'+str(-score)+'</td><td>'+str(time)+'</td>'
		row = table[uidx]
		res += ''.join([submissionCell(s, contest.contestType, showLinks) for s in row])
		res += '</tr>'
	res += '</table>'
	return res

@contest_page
def scoreboard(request, contest):
	return render(request, 'scoreboard.html', {'contest': contest, 'scoreboard': makeScoreboard(contest, datetime.now()>contest.endTime, request.user)})

def highlightedCode(submission):
	data = submission.source.read()
	lexer = guess_lexer_for_filename(submission.source.path, data)
	formatter = HtmlFormatter(linenos=True, noclasses=True)
	return highlight(data, lexer, formatter)

@require_login
def viewSubmission(request, subid):
	subs = models.Submission.objects.filter(id=subid)
	if not subs:
		return redirect('cses.views.index')
	submission = subs[0]
	contest = submission.contest
	if datetime.now() <= contest.endTime:
		return redirect('cses.views.index')
	code = highlightedCode(submission)
	return render(request, 'viewsubmission.html', {'submission': submission, 'contest':contest, 'code':code})
