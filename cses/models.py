from django.db import models
from django.contrib.auth.models import User, Group

class Task(models.Model):
	name = models.CharField(max_length=255, unique=True)
	
	def __unicode__(self):
		return self.name

class Input(models.Model):
	task = models.ForeignKey(Task)
	stuff = models.TextField() # placeholder

class Contest(models.Model):
	name = models.CharField(max_length=255, unique=True)
	users = models.ManyToManyField(User, blank=True)
	groups = models.ManyToManyField(Group, blank=True)
	tasks = models.ManyToManyField(Task, blank=True)
	active = models.BooleanField()
	
	def __unicode__(self):
		return self.name

class Submission(models.Model):
	pass

class Result(models.Model):
	pass

class Language(models.Model):
	pass
