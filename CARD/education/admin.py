from django.contrib import admin
from education.models import Course, Lecture

# https://stackoverflow.com/questions/8043881/django-admin-manytomanyfield
class LectureAdmin(admin.ModelAdmin):
    pass

class LectureInline(admin.StackedInline):
    model = Lecture
    filter_horizontal = ('attending',)
    extra = 0

class CourseAdmin(admin.ModelAdmin):
    filter_horizontal = ('student',)
    fieldsets = [
        ('Course information', {'fields': (['name'], ['slug'], ['dataNoseID'],\
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
admin.site.register(Lecture, LectureAdmin)
