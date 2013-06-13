from django.core.management.base import BaseCommand, CommandError

from cses.models import *

class Command(BaseCommand):
	def handle(self, *args, **options):
		for i in TestCase.objects.all():
			print i.input.path
#		submissions = Submission.objects.filter(binary='')
		submissions = Submission.objects.all()
#		submissions = Submission.objects.raw('SELECT * FROM cses_submission WHERE binary IS NULL')
#		submissions = Submission.objects.all()
#		submissions = Submission.objects.raw('SELECT * FROM cses_submission LEFT JOIN cses_result ON(cses_submission.id = cses_result.id) IS NULL')
		for i in submissions:
			pass
#			print 'submission to',i.task,'['+str(i.binary)+']'
#		qs = Submission.objects.raw()
#		Submission.objects.filter(Results.objects.all())
		# TODO: judging process
#		Result.objects.filter(result=0)
		pass
