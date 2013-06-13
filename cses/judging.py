from socket import *
import sys
from threading import *
import models
from django.core.files.base import ContentFile
import cPickle as pickle
import os
import os.path

class Master(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.condition = Condition()
		self.jobs = []
		self.judges = [JudgeHost(j.host) for j in models.JudgeHost.objects.all()]

	def run(self):
		with self.condition:
			while True:
				if self.jobs and self.judges:
					self.startJobs()
				self.condition.wait()

	def startJobs(self):
		# At this point self.condition is already acquired
		for j in self.jobs:
			if not self.judges:
				break
			j.judge = self.judges.pop()
			j.start()
		self.jobs = []

	def addSubmission(self, submission):
		with self.condition:
			print 'New submission'
			self.jobs.append(JudgeSubmission(self, submission))
			self.condition.notify()

class JudgeSubmission(Thread):
	def __init__(self, master, submission):
		Thread.__init__(self)
		self.master = master
		self.submission = submission
		self.judge = None

	def run(self):
		assert self.judge
		language = self.submission.language
		binary = self.judge.runScript([language.compiler, self.submission.source])
		if not binary:
			print 'FAILURE'
			return
		if 'binary' not in binary:
			print 'Compiling failed', binary['log']
			return
		self.submission.binary.save('binary', ContentFile(binary['binary']))
		self.submission.compileResult = binary['log'] if binary['log'] else 'OK'
		self.submission.save()
		task = self.submission.task

		cases = models.TestCase.objects.filter(task=task)
		for case in cases:
			result = models.Result(submission=self.submission, testcase=case, result=-100)
			result.save()
			runRes = self.judge.runScript([language.runner, self.submission.binary, case.input])
			result.stdout.save('stdout', ContentFile(runRes['stdout']))
			result.stderr.save('stderr', ContentFile(runRes['stderr']))
			print 'stderr:',runRes['stderr']
			status = int(runRes['status'])
			if status<0:
				result.result = status
				result.save()
				break
			result.save()
			compareRes = self.judge.runScript([task.evaluator, case.output, result.stdout])
			score = int(compareRes['result'])
			result.result = score
			result.save()
			print 'judging file done with score',score
			if score<0:
				break

		with master.condition:
			master.condition.notify()


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

	def runScript(self, files):
		print 'running script',files
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
		self.sock.send('RUN '+msg+'\n')
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
