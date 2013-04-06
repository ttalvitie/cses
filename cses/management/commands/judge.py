from django.core.management.base import BaseCommand, CommandError

from cses.models import *

class Command(BaseCommand):
	def handle(self, *args, **options):
		# TODO: judging process
		pass