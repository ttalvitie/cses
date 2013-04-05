from threading import *
from socket import *

sock = socket(AF_INET, SOCK_STREAM)
sock.bind((gethostname(), 21094))

while True:
	(csock,addr) = sock.accept()
