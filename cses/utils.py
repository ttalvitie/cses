"""Utility functions."""

from cses.models import *
from django.db.models import Q
from django.shortcuts import redirect

def getUserContests(user):
	"""Get queryset of contests available for 'user'."""
	query = Q(active=True) & (Q(users=user) | Q(groups__in=user.groups.all()))
	return Contest.objects.filter(query).distinct()

def require_login(func):
	"""Decorator for views that require login."""
	def wrapper(request, *args, **kwargs):
		if request.user.is_authenticated():
			return func(request, *args, **kwargs)
		else:
			return redirect('cses-login')
	return wrapper

def contest_page(func):
	"""Decorator for contest pages. Automatically parses and validates
	contest id and passes it as second parameter."""
	@require_login
	def wrapper(request, contest_id, *args, **kwargs):
		contest_id = int(contest_id)
		matches = getUserContests(request.user).filter(id=contest_id)
		if len(matches) == 0:
			return redirect('cses-index')
		contest = matches[0]
		
		return func(request, contest, *args, **kwargs)
	return wrapper
