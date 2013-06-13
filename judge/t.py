#!/usr/bin/python2
from judgeconn import *
from socket import *

j = JudgeHost(gethostname())
files = ['test.sh', 'asd']
a = j.runScript(files)
print a.status
while a.status=='running':
	pass
print a.status
