from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

import datetime

class StudentManager(models.Manager):
    def get_query_set(self):
        return self.filter(groups__name='Student')

class Student(User):
    class Meta:
        proxy = True

class Course(models.Model):
    name = models.CharField(_('Name'), max_length=100, unique=True)
    #slug = models.SlugField()
    dataNoseID = models.DecimalField(_('DataNose ID'), max_digits=7,\
            decimal_places=0, unique=True)
    catalogID = models.CharField(_('Catalog Number'), max_length=10,\
            unique=True)
    description = models.TextField(_('Description'))
    coordinator = models.CharField(_('Coordinator'), max_length=100)
    student = models.ManyToManyField('Student', null = True, blank = True, \
            related_name = _('StudentCourses'))
    #tutor = models.ManyToManyField('Tutor', null = True, blank = True, related_name = _('Tutor courses'))
    created = models.DateTimeField(auto_now_add = True)
    updated = models.DateTimeField(auto_now = True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = ('Course')
        verbose_name_plural = ('Courses')

    def dataDict(self):
        data = {'name': self.name, 'dataNoseID':self.dataNoseID, \
                'catalogID': self.catalogID, 'description': self.description, \
                'coordinator': self.coordinator}
        return data

class Lecture(models.Model):
    course = models.ForeignKey(Course)
    date = models.DateTimeField(_('Date'))
    lecturers = models.CharField(_('Lecturers'), max_length=150)
    abstract = models.TextField(_('Abstract'))
    TYPES = (('I', _('Programme Information')),
            ('A', _('Alumni Lecture')),
            ('T', _('Guided Tour')),
            ('R', _('Regular')))
    classification = models.CharField(_('Type'), max_length=1, choices=TYPES)
    created = models.DateTimeField(auto_now = True)
    updated = models.DateTimeField(auto_now_add = True)
    attending = models.ManyToManyField('Student', null = True, blank = True, \
            related_name = _('LectureStudents'))

    def __unicode__(self):
        return u'%s on %s' % (self.course, self.date.strftime("%s at %sh" % \
            ("%B %d, %Y", "%H:%M")))

    class Meta:
        verbose_name = ('Lecture')
        verbose_name_plural = ('Lectures')

    def dataDict(self):
        data = {'course': self.course, 'date': self.date, 'lecturers':\
                self.lecturers, 'abstract': self.abstract, 'classification':\
                self.classification}
        return data

  #def register_as_attending(self, student_id):
  #    self.attending +=
