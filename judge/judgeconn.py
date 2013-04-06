#!/usr/bin/python2
from socket import *
import sys
from threading import *

def sendFile(sock, filename, check):
	""" Send contents of file to sock """
	size = 0
	sock.send('SEND '+check+' '+str(size)+'\n')

class JudgeHost:
	def __init__(s, addr):
		s.s = socket(AF_INET, SOCK_STREAM)
		s.s.connect((addr, 21094))
		s.buf = ''
		pass

	def runScript(s, files):
		a = Action(s, files)
		a.start()
		return a

	def getLine(s):
		while '\n' not in s.buf:
			data = s.s.recv(1024)
			if not data:
				return None
			s.buf += data
		res,s.buf = s.buf.split('\n', 1)
		return res

	def getData(s, size):
		while len(s.buf) < size:
			s.buf += s.s.recv(1024)
		res = s.buf[:size]
		s.buf = s.buf[size:]
		return res

class Action(Thread):
	def __init__(s, judge, files):
		Thread.__init__(s)
		s.j = judge
		s.files = files
		s.status = 'running'
		s.output = None

	def run(s):
		msg = ' '.join([f[1] for f in s.files])
		j = s.j
		sock = j.s
		sock.send("HAS " + msg + '\n')
		resline = j.getLine()
		res = map(bool, map(int, resline.split(' ')))
		print 'res',resline,res
		for i in xrange(len(s.files)):
			if not res[i]:
				f = s.files[i]
				print 'sending file',f
				sendFile(sock, f[0], f[1])
				res = j.getLine()
				if res!='OK':
					s.status = 'send files fail'
					return
		msg = ' '.join([f[0]+' '+f[1] for f in s.files])
		sock.send('RUN '+msg+'\n')
		res = j.getLine().split(' ')
		if res[0]!='OK':
			s.status = 'running failed'
			return
		size = int(res[1])
		s.status = 'ok'
		sock.output = s.j.getData(size)
