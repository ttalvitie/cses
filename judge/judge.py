#!/usr/bin/python2
from threading import *
from socket import *
import os.path
import sha
import tempfile
import shutil
import os
from subprocess import *
from stat import *

def getLine(s, buf):
	while '\n' not in buf:
		get = s.recv(1024)
		print 'data: '+get
		if not get:
			return (None,None)
		buf += get
	return buf.split('\n', 1)

def hasFile(f):
	return os.path.exists(f)

def readFile(s, buf, size, check):
	check = check.lower()
	sh = sha.new()
	try:
		f = open(check, 'w')
		count = 0
		while count + len(buf) < size:
			sh.update(buf)
			f.write(buf)
			buf = s.recv(1024)
		remain = size-count
		sh.update(buf[:remain])
		f.write(buf[:remain])

		if sh.hexdigest().lower()==check:
			s.send('OK\n')
		else:
			print "checksum doesn't match:",check,sh.hexdigest().lower()
			s.send('FAIL\n')
		return buf[remain:]
	finally:
		if sh.hexdigest().lower()!=check:
			os.remove(check)

def runCommand(files):
	# TODO: sandbox
	try:
		td = tempfile.mkdtemp()
		for (name,check) in files:
			if not os.path.exists(check):
				return None
			shutil.copyfile(check, os.path.join(td, name))
		script = os.path.join(td, files[0][0])
		print 'running',script
		os.chmod(script, 0700)
		proc = Popen([script], stdout=PIPE)
		out = proc.communicate()[0]
		return out
#		os.system(script)
	except OSError:
		print 'Running script failed'
	finally:
		shutil.rmtree(td)

def handleLine(s, l, buf):
	print 'got line '+l
	parts = l.split(' ')
	cmd = parts[0]
	if cmd=='PING':
		s.send("PONG\n")
	elif cmd=='HAS':
		res = ' '.join((str(int(hasFile(x))) for x in parts[1:]))
		s.send(res+'\n')
	elif cmd=='SEND':
		checksum = parts[1]
		length = int(parts[2])
		buf = readFile(s, buf, length, checksum)
	elif cmd=='RUN':
		cnt = len(parts)/2
		files = [(parts[2*i+1],parts[2*i+2]) for i in xrange(cnt)]
		out = runCommand(files)
		if out:
			s.send("OK "+str(len(out))+'\n'+out)
		else:
			s.send("FAIL\n")
	else:
		print 'Unknown command '+cmd
		s.send('FAIL\n')
	return buf

def handleSocket(s, addr):
	buf = ''
	while True:
		(line,buf) = getLine(s, buf)
		if not line:
			break
		buf = handleLine(s, line, buf)
	print 'disconnect'

sock = socket(AF_INET, SOCK_STREAM)
sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
host = gethostname()
print "binding to",host
sock.bind((host, 21094))
sock.listen(5)

while True:
	(csock,addr) = sock.accept()
	t = Thread(target=handleSocket, args=(csock,addr))
	t.start()
