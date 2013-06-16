from socket import *
import sys
from threading import *
import models
from django.core.files.base import ContentFile
import cPickle as pickle
import os
import os.path
from result import Result
import time

def addJudge(host, master):
	print 'Trying to connect to judgehost'
	while True:
		try:
			jhost = JudgeHost(host)
			print 'Connect to judgehost succeeded'
			master.addJudge(jhost)
			break
		except:
			time.sleep(5)

class Master(Thread):
	def __init__(self):
		Thread.__init__(self)
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
			job = self.jobs.pop()
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
		if 'binary' not in binary:
			print 'Compiling failed', binary['log']
			self.submission.judgeResult = Result.COMPILE_ERROR
			self.submission.compileResult = binary['log']
			return False
		self.submission.binary.save('binary', ContentFile(binary['binary']))
		self.submission.compileResult = binary['log'] if binary['log'] else 'OK'
		self.submission.judgeResult = Result.JUDGING
		return True

	def run(self):
		assert self.judge
		# TODO: do only necessary work when restarting judge
		try:
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
			print 'JUDGING FAILED', sys.exc_info()[0]
#			self.submission.judgeResult = Result.INTERNAL_ERROR
#			self.judge.reconnect()
			self.submission.judgeResult = Result.PENDING
			self.submission.save()
			self.master.addJob(self)
			addJudge(self.judge.host, self.master)

	def judgeCases(self, cases):
		task = self.submission.task
		language = self.submission.language
		minScore = 1000000
		memory = 150*1000 if language.name!='java' else 0
		for case in cases:
			result = models.Result(submission=self.submission, testcase=case, result=Result.JUDGING, time=0, memory=0)
			result.save()
			runRes = self.judge.runScript([language.runner, self.submission.binary, case.input], task.timeLimit, memory)
			result.stdout.save('stdout', ContentFile(runRes['stdout']))
			result.stderr.save('stderr', ContentFile(runRes['stderr']))
			print 'stderr:',runRes['stderr']
			status = int(runRes['status'])
			if runRes['_retval']<0:
				print 'bad retval',runRes['_retval']
				status = runRes['_retval']
			if status<0:
				result.result = status
				self.submission.judgeResult = status
				result.save()
				minScore = status
				break
			result.save()
			compareRes = self.judge.runScript([task.evaluator, case.output, result.stdout], 10)
			score = int(compareRes['result'])
			result.result = score
			result.save()
			print 'judging file done with score',score
			minScore = min(minScore, score)
			if score<0:
				break
		self.submission.judgeResult = minScore


def sendFile(sock, filename, fileField):
	""" Send contents of file to sock """
	sock.send('SEND '+filename+' '+str(fileField.size)+'\n')
	sock.send(fileField.read())

def remoteFileName(name):
	mid = 'cses_files/'
	pos = name.find(mid)
	# FIXME: this replacement might result in different paths becoming the same
	return name[pos:].replace(' ', '__')

def filePath(f):
	return f.path
#	if hasattr(f, 'path'):
#		return f.path
#	return os.path.abspath(f.name)

class JudgeHost:
	def __init__(self, addr):
		self.sock = socket(AF_INET, SOCK_STREAM)
		self.sock.connect((addr, 21094))
		self.buf = ''
		self.addr = addr

	def reconnect(self):
		self.sock.close()
		self.sock = socket(AF_INET, SOCK_STREAM)
		self.sock.connect((self.addr, 21094))

	def runScript(self, files, time, memory=150*1000):
		print 'running script',files,time,memory
		paths = map(filePath, files)
		remotePaths = map(remoteFileName, paths)
		msg = ' '.join(remotePaths)
		self.sock.send("HAS " + msg + '\n')
		resline = self.getLine()
		res = map(bool, map(int, resline.split(' ')))
		print 'res',resline,res, len(files), len(res)
		for i in xrange(len(files)):
			if not res[i]:
				f = files[i]
				print 'sending file',f.path
				sendFile(self.sock, remotePaths[i], f)
				line = self.getLine()
				if line!='OK':
					return
#		msg = ' '.join([f[0]+' '+f[1] for f in files])
		self.sock.send('RUN '+str(time)+' '+str(memory)+' '+msg+'\n')
		res = self.getLine().split(' ')
		if res[0]!='OK':
			print 'Exec failure:',res
			return
		size = int(res[1])
		return pickle.loads(self.getData(size))

	def getLine(self):
		while '\n' not in self.buf:
			data = self.sock.recv(1024)
			if not data:
				raise IOError('No data received from connection')
				return None
			self.buf += data
		res,self.buf = self.buf.split('\n', 1)
		return res

	def getData(self, size):
		while len(self.buf) < size:
			self.buf += self.sock.recv(1024)
		res = self.buf[:size]
		self.buf = self.buf[size:]
		return res

	def ping(self):
		print 'pinging'
		self.sock.send('PING\n')
		res = self.getLine()
		return res=='PONG'


print('Starting judge master thread')
master = Master()
master.daemon = True
master.start()
