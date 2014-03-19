from django.contrib import admin
from education.models import Course, Lecture

class LectureInline(admin.StackedInline):
    model = Lecture
    extra = 1

class CourseAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Course name', {'fields': (['name'], ['dataNoseID'], \
                ['catalogID'], ['description'], ['coordinator'])}),
    ]
    list_display = ('name', 'dataNoseID', 'catalogID', 'description', \
            'coordinator')
    list_filter = ['name']
    search_fields = ['name']
    inlines = [LectureInline]


#class LectureAdmin(admin.ModelAdmin):
#    fieldsets = [
#        (None,               {'fields': ['course']}),
#        ('Lecture information', {'fields': (['date'], ['lecturers'],\
#                ['abstract'], ['classification']) })
#    ]
#    list_display = ('course', 'date', 'lecturers', 'abstract', \
#            'classification')
#    list_filter = ['date']
#    search_fields = ['date']

admin.site.register(Course, CourseAdmin)
#admin.site.register(Lecture, LectureAdmin)
