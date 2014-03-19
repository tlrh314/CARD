from django.db import models
import datetime
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from registration.models import RegistrationProfile

class Course(models.Model):
    name = models.CharField(_('Name'), max_length=100, unique=True)
    dataNoseID = models.DecimalField(_('DataNose ID'), max_digits=7,\
            decimal_places=0, unique=True)
    catalogID = models.CharField(_('Catalog Number'), max_length=10,\
            unique=True)
    description = models.TextField(_('Description'))
    coordinator = models.CharField(_('Coordinator'), max_length=100)

    def __unicode__(self):
        return self.name


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
    TYPES = (('I', _('Informatie studie')),
            ('A', _('Alumnilezing')),
            ('R', _('Rondleiding')),
            ('N', _('Normaal')))
    classification = models.CharField(_('Type'), max_length=1, choices=TYPES)

    students = model.ForeignKey(Students)

    def __unicode__(self):
        return self.course

    def dataDict(self):
        data = {'course': self.course, 'date': self.date, 'lecturers':\
                self.lecturers, 'abstract': self.abstract, 'classification':\
                self.classification}
        return data
