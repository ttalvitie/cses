#!/usr/bin/python2
from threading import *
from socket import *
import os.path
import tempfile
import shutil
import os
from subprocess import *
from stat import *
import cPickle as pickle
import resource
import sys
import time

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

def readFile(s, buf, size, name):
	dirname = os.path.dirname(name)
	if dirname and not os.path.exists(dirname):
		os.makedirs(dirname)
	with open(name, 'w') as f:
		count = 0
		while count + len(buf) < size:
			count += len(buf)
			f.write(buf)
			buf = s.recv(1024)
		remain = size-count
		f.write(buf[:remain])
		return buf[remain:]

#def setLimits():
#	resource.setrlimit(resource.RLIMIT_CPU, (1,1))
#	memlimit = 100*1024*1024 # TODO: specify in some config file etc.
#	resource.setrlimit(resource.RLIMIT_VMEM, (memlimit,memlimit))

def setPathPermission(path, perm):
	try:
		while path!='/':
			os.chmod(path, perm)
			path = os.path.dirname(path)
	except OSError:
		pass

# TODO: get as parameter

runBoxed = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'run_boxed.sh')

def runCommand(files, maxTime, maxMemory):
	origDir = os.getcwd()
	try:
		td = tempfile.mkdtemp()
		for name in files:
			if not os.path.exists(name):
				print 'Missing required file',name
				return None
			# TODO: could we avoid copying and just give read permissions to files?
#			print 'copying',name,'to',os.path.join(td,name)
			dest = os.path.join(td, name)
			destdir = os.path.dirname(dest)
			if not os.path.exists(destdir):
				os.makedirs(destdir)
			shutil.copy(name, os.path.join(td, name))
		tfiles = [os.path.join(td, f) for f in files]
		print 'running',tfiles
		for f in tfiles:
			os.chmod(f, 0777)
		outdir = os.path.join(td, 'out')
		os.mkdir(outdir)
		os.chdir(outdir)
		setPathPermission(outdir, 0111)
		os.chmod(td, 0777)
		os.chmod(outdir, 0777)
#		proc = Popen(tfiles, stdout=PIPE)
		saferun = ['sudo', '-u', 'judgerun', runBoxed, str(int(maxTime+1)), str(maxMemory)]
		startTime = time.time()
		retval = call(saferun + tfiles)
		usedTime = time.time() - startTime
		if usedTime > maxTime:
			print 'TLE'
			retval = -2
		elif retval!=0:
			retval = -3
#		proc = Popen(tfiles, stdout=PIPE, preexec_fn=setLimits)
#		out = proc.communicate()[0]
#		return out
#		proc.wait()
		outfiles = [f for f in os.listdir(outdir) if os.path.isfile(f)]
		res = dict([(f,open(f,'r').read()) for f in outfiles])
		res['_retval'] = retval
		return res
	except OSError as e:
		print 'Running script failed',e
	finally:
		shutil.rmtree(td)
		os.chdir(origDir)

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
		name = parts[1]
		length = int(parts[2])
		buf = readFile(s, buf, length, name)
		s.send('OK\n')
	elif cmd=='RUN':
		time = float(parts[1])
		memory = int(parts[2])
		files = parts[3:]
		print 'Starting with files',files
		out = runCommand(files, time, memory)
		if out:
			print 'run ok',out.keys()
			outs = pickle.dumps(out)
			s.send("OK "+str(len(outs))+'\n'+outs)
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
	t.daemon = True
	t.start()
