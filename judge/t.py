#!/usr/bin/python2
from judgeconn import *
from socket import *

j = JudgeHost(gethostname())
files = [('asd','da39a3ee5e6b4b0d3255bfef95601890afd80709')]
a = j.runScript(files)
print a.status
while a.status=='running':
	pass
print a.status
