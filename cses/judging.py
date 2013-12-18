import xmlrpclib
from xmlrpclib import Binary
import sys
from threading import *
from django.core.files.base import ContentFile
import os
import os.path
import time
import traceback
import models
from result import Result
from hashlib import sha1
import cPickle
from django.conf import settings

def addJudge(host, master):
	print 'Trying to connect to judgehost'
	while True:
		try:
			jhost = JudgeHost(host)
			jhost.ping()
			print 'Connect to judgehost succeeded'
			master.addJudge(jhost)
			break
		except:
			time.sleep(5)

class Master(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.daemon = True
		self.condition = Condition()
		self.jobs = []
		# TODO: check for judges not only at start
#		self.judges = [JudgeHost(j.host) for j in models.JudgeHost.objects.filter(active=True)]
		self.judges = []
		for j in models.JudgeHost.objects.filter(active=True):
			t = Thread(target=addJudge, args=(j.host, self))
			t.daemon = True
			t.start()
#			addJudge(j.host, self)
#		self.reservedJudges = []

	def run(self):
		with self.condition:
			while True:
				self.startJobs()
				self.condition.wait()

	def startJobs(self):
		# At this point self.condition is already acquired
		while self.jobs and self.judges:
			job = self.jobs[0]
			self.jobs = self.jobs[1:]
			job.judge = self.judges.pop()
			job.start()

	def addSubmission(self, submission):
		self.addJob(JudgeSubmission(self, submission))

	def addJob(self, job):
		with self.condition:
			self.jobs.append(job)
			self.condition.notify()

	def addJudge(self, judge):
		with self.condition:
			self.judges.append(judge)
			self.condition.notify()

class JudgeSubmission(Thread):
	def __init__(self, master, submission):
		Thread.__init__(self)
		self.daemon = True
		self.master = master
		self.submission = submission
		self.judge = None

	def compileSubmission(self):
		language = self.submission.language
		binary = self.judge.runScript([language.compiler, self.submission.source], 30, 0)
		if not binary:
			print 'FAILURE'
			self.submission.judgeResult = Result.INTERNAL_ERROR
			return False
		self.submission.compileResult= unicode(binary['log'] if 'log' in binary else 'OK', errors='ignore')
		if 'binary' not in binary:
			print 'Compiling failed'
			self.submission.judgeResult = Result.COMPILE_ERROR
			return False
		self.submission.binary.save('binary', ContentFile(binary['binary']))
		return True

	def run(self):
		assert self.judge
		# TODO: do only necessary work when restarting judge
		try:
			self.judge.ping()
		except:
			addJudge(self.judge.addr, self.master)
			self.master.addSubmission(self.submission)
			return

		try:
			self.submission.judgeResult = Result.JUDGING
			self.submission.save()
			compileRes = self.compileSubmission()
			self.submission.save()
			if not compileRes:
				self.master.addJudge(self.judge)
				return
			task = self.submission.task
			cases = models.TestCase.objects.filter(task=task)
			self.judgeCases(cases)

			self.submission.save()
			self.master.addJudge(self.judge)
			print 'judging finished'
#		except IOError as e:
		except:
			print 'JUDGING FAILED'
			traceback.print_exc()
			self.submission.judgeResult = Result.INTERNAL_ERROR
			self.submission.save()
#			self.master.addSubmission(self.submission)
			addJudge(self.judge.addr, self.master)

	def judgeCases(self, cases):
		task = self.submission.task
		language = self.submission.language
		totalScore = 0
		memory = 150*1000 if language.name!='java' else 0
		contestType = self.submission.contest.contestType
		for case in cases:
			result = makeResult(self.submission, case)
			runRes = self.judge.runScript([language.runner, self.submission.binary, case.input], task.timeLimit, memory)
			if not 'stdout' in runRes or not 'stderr' in runRes or not 'status' in runRes:
				status = Result.RUNTIME_ERROR
			else:
				result.stdout.save('stdout', ContentFile(runRes['stdout']))
				result.stderr.save('stderr', ContentFile(runRes['stderr']))
				result.time = runRes['_time']
				print 'stderr:',runRes['stderr']
				status = int(runRes['status'])
			if runRes['_retval']<0:
				print 'bad retval',runRes['_retval']
				status = runRes['_retval']
			if status<0:
				result.result = status
				self.submission.judgeResult = status
				result.save()
				if contestType==models.Contest.Type.ICPC:
					totalScore = status
					break
				continue
			result.save()
			compareRes = self.judge.runScript([task.evaluator, case.output, result.stdout, case.input], 10)
			score = int(compareRes['result'])
			result.result = score
			result.save()
			print 'judging file done with score',score
			if score>=0:
				totalScore += score
			elif contestType==models.Contest.Type.ICPC:
				totalScore = score
				break
		if totalScore>0 and contestType==models.Contest.Type.ICPC:
			totalScore = 1
		self.submission.judgeResult = totalScore

def makeResult(submission, case):
	args={'result':Result.JUDGING, 'time':0, 'memory':0}
	keyArgs={'submission':submission, 'testcase':case}
	try:
		result = models.Result.objects.get(**keyArgs)
		result.save()
	except models.Result.DoesNotExist:
		args.update(keyArgs)
		result = models.Result(**args)
		result.save
	return result

def remoteFileName(name):
	mid = 'cses_files/'
	pos = name.find(mid)
	# FIXME: this replacement might result in different paths becoming the same
	return str(name[pos:].replace(' ', '__'))

def filePath(f):
	return f.path
#	if hasattr(f, 'path'):
#		return f.path
#	return os.path.abspath(f.name)

judgeKey = ''
try:
	judgeKey = settings.JUDGE_KEY
except AttributeError:
	pass

class SafeRPC:
	def __init__(self, addr):
		self.proxy = xmlrpclib.ServerProxy(addr, allow_none=True)

	def __getattr__(self, name):
		def safeCall(*args):
			key = sha1(judgeKey + cPickle.dumps(args)).hexdigest()
			method = self.proxy.__getattr__(name)
			return method(key, *args)
		return safeCall

class JudgeHost:
	def __init__(self, addr):
		self.addr = addr
		self.reconnect()

	def reconnect(self):
		self.rpc = SafeRPC('http://'+self.addr+':21095/')

	def runScript(self, files, time, memory=150*1000):
		print 'running script',files,time,memory
		paths = map(filePath, files)
		remotePaths = map(remoteFileName, paths)
		res = self.rpc.hasFiles(remotePaths)
		print 'res',res, len(files), len(res)
		for i in xrange(len(files)):
			if not res[i]:
				f = files[i]
				print 'sending file',f.path
				self.rpc.sendFile(remotePaths[i], Binary(f.read()))
		res = self.rpc.runProgram(remotePaths, time, memory)
		for i in res:
			if isinstance(res[i], Binary):
				res[i] = res[i].data
		return res

	def ping(self):
		assert self.rpc.ping()=='pong', 'PING failed'


print('Starting judge master thread')
master = Master()
master.start()
