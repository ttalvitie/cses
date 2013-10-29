#!/usr/bin/python2
import xmlrpclib
from xmlrpclib import Binary
from SimpleXMLRPCServer import SimpleXMLRPCServer
from socket import gethostname
import os.path
import tempfile
import shutil
import os
from subprocess import *
from stat import *
import sys
import time

def setPathPermission(path, perm):
	try:
		while path!='/':
			os.chmod(path, perm)
			path = os.path.dirname(path)
	except OSError:
		pass

# TODO: get as parameter
origDir = os.path.dirname(os.path.abspath(sys.argv[0]))
runBoxed = os.path.join(origDir, 'run_boxed.sh')
restrictSyscalls = os.path.join(origDir, 'restrict_syscalls')


def runProgram(files, maxTime, maxMemory):
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
				setPathPermission(destdir, 0711)
			shutil.copy(name, os.path.join(td, name))
		tfiles = [os.path.join(td, f) for f in files]
		print 'running',tfiles
		for f in tfiles:
			os.chmod(f, 0777)
		outdir = os.path.join(td, 'out')
		os.mkdir(outdir)
		os.chdir(outdir)
		setPathPermission(outdir, 0711)
		os.chmod(td, 0777)
		os.chmod(outdir, 0777)
#		proc = Popen(tfiles, stdout=PIPE)
		saferun = ['sudo', '-u', 'judgerun', runBoxed, str(int(maxTime+1)), str(maxMemory), restrictSyscalls]
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
		for f in os.listdir(outdir):
			call(['sudo', '-u', 'judgerun', 'chmod', '-R', '777', f])
		outfiles = [f for f in os.listdir(outdir) if os.path.isfile(f)]
		res = dict([(f,Binary(open(f,'r').read())) for f in outfiles])
		res['_retval'] = retval
		res['_time'] = usedTime
		return res
	except OSError as e:
		print 'Running script failed',e
	finally:
		shutil.rmtree(td)
		os.chdir(origDir)

def ping():
	return 'pong'

def hasFiles(names):
	return [os.path.exists(x) for x in names]

def sendFile(name, data):
	dirname = os.path.dirname(name)
	if dirname and not os.path.exists(dirname):
		os.makedirs(dirname)
	with open(name, 'w') as f:
		f.write(data.data)

host = gethostname()
server = SimpleXMLRPCServer((host, 21095), allow_none=True)
for i in [ping, hasFiles, sendFile, runProgram]:
	server.register_function(i, i.__name__)
print 'Entering server loop'
server.serve_forever()
