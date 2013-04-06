"""Utility functions for contests."""

from cses.models import *
from django.db.models import Q

def getUserContests(user):
	"""Get queryset of contests available for 'user'."""
	query = Q(active=True) & (Q(users=user) | Q(groups=user.groups.all()))
	return Contest.objects.filter(query)
