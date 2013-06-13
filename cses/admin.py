from django.contrib import admin
from cses.models import *
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

admin.site.register(Contest)
admin.site.register(Language)
admin.site.register(Submission)
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
