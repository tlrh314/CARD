from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from CARD.settings import TYPES

import datetime
from django.utils import timezone

class StudentManager(models.Manager):
    def get_query_set(self):
        return self.filter(groups__name='Student')

class Student(User):
    class Meta:
        proxy = True

class TeacherManager(models.Manager):
    def get_query_set(self):
        return self.filter(groups__name='Teacher')

class Teacher(User):
    class Meta:
        proxy = True

class CourseManager(models.Manager):
    def create_course(self, name):
        course = self.create(title=title)
        return course

class Course(models.Model):
    name = models.CharField(_('Full Name'), max_length=100, unique=True)
    slug = models.SlugField(_('Abbreviation'), max_length=15, \
            unique=True, blank=True)
    dataNoseID = models.DecimalField(_('DataNose ID'), max_digits=7,\
            decimal_places=0, unique=True)
    catalogID = models.CharField(_('Catalog Number'), max_length=10,\
            unique=True, blank=True)
    description = models.TextField(_('Description'))
    coordinator = models.CharField(_('Coordinator'), max_length=100)
    # change student to enrolled?
    student = models.ManyToManyField('Student', null = True, blank = True, \
            related_name = _('StudentCourses'))
    teacher = models.ManyToManyField('Teacher', null = True, blank = True, \
            related_name = _('TeacherCourses'))
    created = models.DateTimeField(auto_now_add = True)
    updated = models.DateTimeField(auto_now = True)

    objects = CourseManager()

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = ('Course')
        verbose_name_plural = ('Courses')

class LectureManager(models.Manager):
    # Only require course, date, title and classification.
    def create_lecture(self, course_pk, date, title, classification, slug):
        lecture = self.create(course_id=course_pk, date=date,title=title,\
                classification=classification, slug=slug)
        return lecture

class Lecture(models.Model):
    course = models.ForeignKey(Course)
    date = models.DateTimeField(_('Date'))
    lecturers = models.CharField(_('Lecturers'), max_length=150, blank=True)
    title = models.CharField(_('Full Title'), max_length=150)
    slug = models.SlugField(_('Abbreviation'), max_length=15, \
            unique = True, blank=True)
    abstract = models.TextField(_('Abstract'), blank=True)
    classification = models.CharField(_('Type'), max_length=1, choices=TYPES)
    created = models.DateTimeField(auto_now = True)
    updated = models.DateTimeField(auto_now_add = True)
    attending = models.ManyToManyField('Student', null = True, blank = True, \
            related_name = _('LectureStudents'))

    objects = LectureManager()

    def __unicode__(self):
        return u'%s on %s' % (self.course, self.date.strftime("%s" % \
            ("%d %b %Y")))

    class Meta:
        verbose_name = ('Lecture')
        verbose_name_plural = ('Lectures')

    def in_future(self):
        now = timezone.now()
        return now <= self.date


class Barcode(models.Model):
    course = models.ForeignKey(Course)
    student = models.ManyToManyField('Student', null = True, blank = True, \
            related_name = _('barcode'))
