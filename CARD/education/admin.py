from django.contrib import admin
from education.models import Course, Lecture

class LectureInline(admin.StackedInline):
    model = Lecture
    extra = 0

class CourseAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Course information', {'fields': (['name'], ['dataNoseID'], \
                ['catalogID'], ['description'], ['coordinator'], ['student'])}),
        ]
    list_display = ('name', 'dataNoseID', 'catalogID', 'description', \
            'coordinator', 'created', 'updated')
    list_filter = ['name']
    search_fields = ['name']
    inlines = [LectureInline]

    def has_add_permission(self, request):
        return request.user.is_superuser or \
                request.user.groups.filter(name='Coordinator').exists()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or \
                request.user.groups.filter(name='Coordinator').exists()

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or \
                request.user.groups.filter(name='Coordinator').exists()

admin.site.register(Course, CourseAdmin)
