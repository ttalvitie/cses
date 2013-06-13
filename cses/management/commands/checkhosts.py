from django.core.management.base import BaseCommand, CommandError

from cses.models import *
import cses.judging as judging

class Command(BaseCommand):
	def handle(self, *args, **options):
		for j in JudgeHost.objects.filter(active=True):
			print j.name,j.host
			host = judging.JudgeHost(j.host)
			print host.ping()
