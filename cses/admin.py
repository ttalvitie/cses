from django.contrib import admin
from cses.models import *
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import guess_lexer_for_filename
import sys

admin.site.register(Contest)
admin.site.register(Language)
admin.site.register(JudgeHost)

class TestCaseInline(admin.StackedInline):
	model = TestCase
class TaskAdmin(admin.ModelAdmin):
	inlines = [TestCaseInline]

admin.site.register(Task, TaskAdmin)

# Make user admin allow filtering by groups.
class MyUserAdmin(UserAdmin):
    list_filter = UserAdmin.list_filter + ('groups',)

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)

class ResultInline(admin.TabularInline):
	model = Result
	readonly_fields = ('input','output','correct','result')
	exclude = ('testcase', 'stdout', 'stderr')
	def input(self, instance):
		return instance.testcase.input.read()
	def output(self, instance):
		return instance.stdout.read()
	def correct(self, instance):
		return instance.testcase.output.read()
	input.short_description = 'stdin'
	output.short_description = 'stdout'
	correct.short_description = 'correct'

	def has_add_permission(self, request):
		return False
	def has_delete_permission(self, request, obj):
		return False

class SubmissionAdmin(admin.ModelAdmin):
	inlines = [ResultInline]
	exclude = ('binary',)
	readonly_fields = ('task', 'contest', 'user', 'language', 'time', 'source', 'sourceText', 'compileResult', 'judgeResult')

	def sourceText(self, instance):
		data = instance.source.read()
		lexer = guess_lexer_for_filename(instance.source.path, data)
		formatter = HtmlFormatter(linenos=True, noclasses=True)
		return highlight(data, lexer, formatter)
	sourceText.short_description = 'Source'
	sourceText.allow_tags = True
#admin.site.register(Submission)
admin.site.register(Submission, SubmissionAdmin)
