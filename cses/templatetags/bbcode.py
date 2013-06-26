from postmarkup import *
from django import template
from django.conf import settings
from django.utils.encoding import smart_str, force_unicode
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def bbcode(value):
	return mark_safe(render_bbcode(value))
bbcode.is_save = True

@register.filter
def strip_bbcode(value):
	return mark_safe(strip_bbcode(value))
bbcode.is_save = True
