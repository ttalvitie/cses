from django.db import models
from django.contrib.auth.models import User, Group
from django.core.files.storage import FileSystemStorage

from django.conf import settings
fs = FileSystemStorage(location=settings.CSES_FILES_DIR)

#class File

class Task(models.Model):
	name = models.CharField(max_length=255, unique=True)
	evaluator = models.FileField(storage=fs, upload_to='task_evaluators/')
	
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
	tasks = models.ManyToManyField(Task, blank=True)
	active = models.BooleanField()
	
	def __unicode__(self):
		return self.name

class Submission(models.Model):
	task = models.ForeignKey(Task)
	contest = models.ForeignKey(Contest)
	user = models.ForeignKey(User)
	language = models.ForeignKey(Language)
	source = models.FileField(storage=fs, upload_to='submission_sources/')
	binary = models.FileField(storage=fs, upload_to='submission_binaries/', null=True)
	compileResult = models.TextField(null=True)

class Result(models.Model):
	submission = models.ForeignKey(Submission)
	testcase = models.ForeignKey(TestCase)
	stdout = models.FileField(storage=fs, upload_to='submission_outputs/')
	stderr = models.FileField(storage=fs, upload_to='submission_outputs/')
	result = models.IntegerField()
	
	class Meta:
		unique_together = ('submission', 'testcase')

class JudgeHost(models.Model):
	name = models.CharField(max_length=255, unique=True)
	host = models.CharField(max_length=255)
	active = models.BooleanField()
