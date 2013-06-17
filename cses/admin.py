from django.contrib import admin
from cses.models import *
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import guess_lexer_for_filename
import sys

admin.site.register(Language)
admin.site.register(JudgeHost)

class TestCaseInline(admin.TabularInline):
	model = TestCase
class SubmissionInline(admin.TabularInline):
	model = Submission
	readonly_fields = ('time', 'contest', 'user', 'language', 'resultString')
	exclude = ('source', 'binary', 'compileResult', 'judgeResult')
	ordering = ('-time',)
	def has_add_permission(self, request):
		return False
	def has_delete_permission(self, request, obj):
		return False
class TaskAdmin(admin.ModelAdmin):
	inlines = [TestCaseInline, SubmissionInline]

admin.site.register(Task, TaskAdmin)

# Make user admin allow filtering by groups.
class MyUserAdmin(UserAdmin):
    list_filter = UserAdmin.list_filter + ('groups',)

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)

class ResultInline(admin.TabularInline):
	model = Result
	readonly_fields = ('input','output','correct','result', 'time')
	exclude = ('testcase', 'stdout', 'stderr', 'memory')
	def input(self, instance):
		return instance.testcase.input.read(1000)
	def output(self, instance):
		return instance.stdout.read(1000)
	def correct(self, instance):
		return instance.testcase.output.read(1000)
	input.short_description = 'stdin'
	output.short_description = 'stdout'
	correct.short_description = 'correct'

	def has_add_permission(self, request):
		return False
	def has_delete_permission(self, request, obj):
		return False

class SubmissionAdmin(admin.ModelAdmin):
	inlines = [ResultInline]
	exclude = ('binary','judgeResult')
	readonly_fields = ('task', 'contest', 'user', 'language', 'time', 'source', 'sourceText', 'compileResult', 'resultString')

	def sourceText(self, instance):
		data = instance.source.read()
		lexer = guess_lexer_for_filename(instance.source.path, data)
		formatter = HtmlFormatter(linenos=True, noclasses=True)
		return highlight(data, lexer, formatter)
	sourceText.short_description = 'Source'
	sourceText.allow_tags = True

	list_display = ('task','user','language','resultString')
	list_display_links = list_display
#admin.site.register(Submission)
admin.site.register(Submission, SubmissionAdmin)

class ContestTaskInline(admin.TabularInline):
	model = ContestTask
class ContestAdmin(admin.ModelAdmin):
	inlines = [ContestTaskInline]
admin.site.register(Contest, ContestAdmin)
