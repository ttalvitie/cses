from django.db import models
from django.contrib.auth.models import User, Group
from django.core.files.storage import FileSystemStorage

from django.conf import settings
import result
fs = FileSystemStorage(location=settings.CSES_FILES_DIR)

#class File

class Task(models.Model):
	name = models.CharField(max_length=255, unique=True)
	evaluator = models.FileField(storage=fs, upload_to='task_evaluators/')
	timeLimit = models.FloatField()
	score = models.IntegerField()

	def __unicode__(self):
		return self.name

class TestCase(models.Model):
	task = models.ForeignKey(Task)
	input = models.FileField(storage=fs, upload_to='testcase_inputs/')
	output = models.FileField(storage=fs, upload_to='testcase_outputs/')

class Language(models.Model):
	name = models.CharField(max_length=255, unique=True)
	compiler = models.FileField(storage=fs, upload_to='language_compilers/')
	runner = models.FileField(storage=fs, upload_to='language_runners/')

	def __unicode__(self):
		return self.name

class Contest(models.Model):
	name = models.CharField(max_length=255, unique=True)
	users = models.ManyToManyField(User, blank=True)
	groups = models.ManyToManyField(Group, blank=True)
	tasks = models.ManyToManyField(Task, through='ContestTask')
	active = models.BooleanField()
	startTime = models.DateTimeField()
	endTime = models.DateTimeField()

	CONTEST_TYPES = ((0, 'ICPC'), (1, 'IOI'))
	contestType = models.IntegerField(choices=CONTEST_TYPES)

	Type = type('Type', (), dict([(b,a) for (a,b) in CONTEST_TYPES]))

	def __unicode__(self):
		return self.name

	def latestSubmits(self):
		submits = Submission.objects.select_related('task', 'user').filter(contest=self).order_by('time')
		res = {}
		for s in submits:
			task = s.task.name
			user = unicode(s.user)
			if task not in res:
				res[task] = {}
			userDict = res[task]
			(_, oldTime, oldCount) = userDict.get(user, (None, 0, 0))
			penalty = result.penaltyTime(s.judgeResult)
			userDict[user] = (s, oldTime+penalty, oldCount+1)
		return res

class ContestTask(models.Model):
	contest = models.ForeignKey(Contest)
	task = models.ForeignKey(Task)
	order = models.IntegerField()

class Submission(models.Model):
	task = models.ForeignKey(Task)
	contest = models.ForeignKey(Contest)
	user = models.ForeignKey(User)
	language = models.ForeignKey(Language)
	source = models.FileField(storage=fs, upload_to='submission_sources/')
	binary = models.FileField(storage=fs, upload_to='submission_binaries/', null=True)
	compileResult = models.TextField(null=True)
	judgeResult = models.IntegerField()
	time = models.DateTimeField()

	def resultString(self):
		if self.judgeResult>=0 and self.contest.contestType==Contest.Type.IOI:
			return self.points()
		return result.toString(self.judgeResult)

	def submitTime(self):
		diff = self.time - self.contest.startTime
		diffSec = diff.seconds + diff.days*24*3600
		return int(diffSec/60)

	def points(self):
		if self.judgeResult<=0:
			return 0
		contest = self.contest
		if contest.contestType==Contest.Type.ICPC:
			return 1
		task = self.task
		count = TestCase.objects.filter(task=task).count()
		return self.judgeResult * task.score / count

	def colorType(self):
		if result.notDone(self.judgeResult):
			return 'sol_notdone'
		if self.judgeResult<=0:
			return 'sol_incorrect'
		if self.contest.contestType==Contest.Type.IOI and self.judgeResult<TestCase.objects.filter(task=self.task).count():
			return 'sol_partial'
		return 'sol_correct'

class Result(models.Model):
	submission = models.ForeignKey(Submission)
	testcase = models.ForeignKey(TestCase)
	stdout = models.FileField(storage=fs, upload_to='submission_outputs/')
	stderr = models.FileField(storage=fs, upload_to='submission_outputs/')
	result = models.IntegerField()
	time = models.FloatField()
	memory = models.IntegerField()

	def resultString(self):
		return result.toString(self.result)

	class Meta:
		unique_together = ('submission', 'testcase')

class JudgeHost(models.Model):
	name = models.CharField(max_length=255, unique=True)
	host = models.CharField(max_length=255)
	active = models.BooleanField()

	def __unicode__(self):
		return self.name

class Comment(models.Model):
	submission = models.ForeignKey(Submission)
	user = models.ForeignKey(User)
	text = models.TextField()
	line = models.IntegerField()
	time = models.DateTimeField()
