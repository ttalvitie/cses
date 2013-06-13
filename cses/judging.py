from socket import *
import sys
from threading import *
import models

class Master(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.condition = Condition()
		self.jobs = []
		self.judges = list(models.JudgeHost.objects.all())

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
			self.jobs.push(JudgeSubmission(self, submission))
			self.condition.notify()

print('Starting judge master thread')
master = Master()
master.start()


class JudgeSubmission(Thread):
	def __init__(self, master, submission):
		Thread.__init__(self)
		self.master = master
		self.submission = submission
		self.judge = None

	def run(self):
		assert self.judge
		language = self.submission.language
		binary = self.judge.runScript([(language.compiler), self.submission.source])
		self.submission.binary = binary
		self.submission.compileResult = 'OK'
		self.submission.save()
		task = self.submission.task

		cases = models.TestCase.objects.filter(task=task)
		for case in cases:
			result = models.Result(submission=submission, testcase=case, result=-100)
			result.save()
			caseRes = self.judge.runScript(language.runner, binary, case.input, case.output)
			intRes = int(caseRes)
			result.result = intRes
			result.save()
			if intRes<0:
				break

		with master.condition:
			master.condition.notify()


def sendFile(sock, filename, fileField):
	""" Send contents of file to sock """
	size = 0
	sock.send('SEND '+filename+' '+str(size)+'\n')
	with fileField.open('rb') as f:
		sock.send(f.read())

def remoteFileName(name):
	mid = 'cses_files/'
	pos = name.find(mid)
	# FIXME: this replacement might result in different paths becoming the same
	return name[pos+len(mid):].replace(' ', '_')

class JudgeHost:
	def __init__(self, addr):
		self.sock = socket(AF_INET, SOCK_STREAM)
		self.sock.connect((addr, 21094))
		self.buf = ''

	def runScript(self, files):
		paths = [f.path for f in files]
		remotePaths = map(remoteFileName, paths)
		msg = ' '.join(removePaths)
		self.sock.send("HAS " + msg + '\n')
		resline = self.getLine()
		res = map(bool, map(int, resline.split(' ')))
		print 'res',resline,res
		for i in xrange(len(files)):
			if not res[i]:
				f = files[i]
				print 'sending file',f.path
				sendFile(self.sock, remotePaths[i], f)
				res = self.getLine()
				if res!='OK':
					return
#		msg = ' '.join([f[0]+' '+f[1] for f in files])
		self.sock.send('RUN '+msg+'\n')
		res = self.getLine().split(' ')
		if res[0]!='OK':
			print 'Exec failure:',res
			return
		size = int(res[1])
		return self.getData(size)

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
