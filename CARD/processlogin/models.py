#from django.db import models
##from redactor.fields import RedactorField
#from HTMLParser import HTMLParser
#from datetime import datetime
#from django.utils import timezone
#from django.contrib.auth.models import User
#import re
#
#ITEM_TYPES = (
#        ('G', 'Good Practice'),
#        ('R', 'Project'),
#        ('E', 'Event'),
#        ('S', 'Glossary'),
#        ('I', 'Information'),
#        ('P', 'Person'),
#        ('Q', 'Question'),
#        )
#
#
#class MLStripper(HTMLParser):
#    def __init__(self):
#        self.reset()
#        self.fed = []
#
#    def handle_data(self, d):
#        self.fed.append(d)
#
#    def get_data(self):
#        return ' '.join(self.fed)
#
#
#def strip_tags(html):
#    s = MLStripper()
#    s.feed(html)
#    return s.get_data()
#
#def cleanup_for_search(raw_text):
#    """
#    Cleanup raw_text to be suited for matching in search.
#    Operations:
#        - Strip HTML tags
#        - Remove newlines, returns and tab characters
#        - Trim double and trailing spaces
#        - Convert to lower case
#        - Remove URLs
#        - Remove email addresses
#    """
#    # Strip HTML tags
#    text = strip_tags(raw_text)
#    # Remove newlines, returns and tab characters
#    text = re.sub(r"[\t\n\r]", "", text)
#    # Trim double and trailing spaces
#    text = re.sub(r" +", " ", text).strip()
#    # Convert to lower case
#    text = text.lower()
#    # Remove URLs
#    text = re.sub(r'\b(https?|ftp)://[^\s/$.?#].[^\s]*\b', "", text)
#    # Remove email addresses
#    text = re.sub(r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}\b', "", text)
#    return text
#
#class Item(models.Model):
#    # Tags linked to this item
#    tags = models.ManyToManyField('Tag', blank=True)
#    # The other items that are linked to this item
#    links = models.ManyToManyField('Item', blank=True)
#    # The comments linked to this item
#    comments = models.ManyToManyField('Comment', blank=True, editable=False)
#    # Whether this item is featured by a moderator
#    featured = models.BooleanField(default=False)
#    # The type of this item, important to know which subclass to load
#    type = models.CharField(max_length=1, choices=ITEM_TYPES, editable=False)
#    # The score of this item, which can be used for ranking of search results
#    score = models.IntegerField(default=0)
#    # The date that this item was created in the database
#    create_date = models.DateTimeField(auto_now=True, editable=False)
#    # The concatenated string representation of each item for free text search
#    searchablecontent = models.TextField(editable=False)
#    # The communities for which the item is visible
#    communities = models.ManyToManyField('Community',
#            default=lambda:[Community.objects.get(pk=1)], related_name='items')
#
#    # Return reference the proper subclass when possible, else return None
#    def downcast(self):
#        # Define links to subclasses
#        subcls = {
#            'P': lambda self: self.person,
#            'G': lambda self: self.goodpractice,
#            'I': lambda self: self.information,
#            'R': lambda self: self.project,
#            'E': lambda self: self.event,
#            'Q': lambda self: self.question,
#            'S': lambda self: self.glossary
#        }
#        # If link to the current subclass is known
#        if self.type in subcls:
#            return subcls[self.type](self)
#        else:
#            return None
#
#    def summary(self):
#        return ""
#
#    def _truncate(self, text, max_len=200):
#        if len(text) > max_len:
#            return strip_tags(text)[:max_len - 2] + "..."
#        return strip_tags(text)
#
#    # Dictionary representation used to communicate the model to the client
#    def dict_format(self, obj={}):
#        # Fill dict format at this level
#        # make sure the pass by reference does not cause unexpected results
#        obj = obj.copy()
#        obj.update({
#            'id': self.id,
#            'type': dict(ITEM_TYPES)[self.type],
#            'tags': [t.dict_format() for t in list(self.tags.all())],
#            'featured': self.featured,
#            'score': self.score,
#            'summary': self.summary(),
#            'create_date': self.create_date,
#            'get_absolute_url': self.downcast().get_absolute_url()
#        })
#        # Attempt to get reference to subclass
#        subcls = self.downcast()
#        # Attempt to let subclasses fill in dict format further
#        if subcls is not None and hasattr(subcls, 'dict_format'):
#            return subcls.dict_format(obj)
#        else:
#            return obj
#
#    def get_absolute_url(self):
#        if self.type in dict(ITEM_TYPES):
#            t = dict(ITEM_TYPES)[self.type].lower().replace(" ", "")
#            return '/' + t + "/" + str(self.id)
#        else:
#            return '/item/' + str(self.id)
#
#    def __unicode__(self):
#        # Attempt to get reference to subclass
#        subcls = self.downcast()
#        if subcls is not None:
#            return subcls.__unicode__()
#        else:
#            return self.searchablecontent[:40]
#
#    def save_dupe(self):
#        super(Item, self).save()
#
#    def save(self, *args, **kwargs):
#        super(Item, self).save(*args, **kwargs)
#
#        # Make link reflexive
#        for link in self.links.all():
#            if link.links.filter(pk=self.pk).count() == 0:
#                link.links.add(self)
#                link.save()
#
#
#
#
#class Person(Item):
#    # Handle to identify this person with
#    handle = models.CharField(max_length=255)
#    # The official title, e.g. `dr.' or `prof.'
#    title = models.CharField(max_length=50, blank=True, default="")
#    # The full name of this person, including first names and family name
#    name = models.CharField(max_length=254)
#    # Short text describing the core of this person
#    headline = models.CharField(max_length=200)
#    # Text describing this person
#    #about = RedactorField(blank=True)
#    # The source of a photo
#    photo = models.URLField(blank=True)
#    # The website of this person
#    website = models.URLField(max_length=255, null=True, blank=True)
#    # The email address of this person
#    email = models.EmailField(null=True)
#    # User corresponding to this person. If user deleted, person remains.
#    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True,
#                                blank=True)
#
#    def __init__(self, *args, **kwargs):
#        super(Person, self).__init__(*args, **kwargs)
#        self.type = 'P'
#
#    def summary(self):
#        return self.headline
#
#    def dict_format(self, obj=None):
#        """Dictionary representation used to communicate the model to the
#client.
#"""
#        if obj is None:
#            return super(Person, self).dict_format()
#        else:
#            obj.update({
#                'handle': self.handle,
#                'title': self.title,
#                'name': self.name,
#                'about': self.about,
#                'photo': self.photo,
#                'website': self.website,
#                'summary': self.summary(),
#                'email': self.email,
#            })
#            return obj
#
#    def __unicode__(self):
#        return "[Person] %s" % (self.name,)
#
#    def save(self, *args, **kwargs):
#        texts = [cleanup_for_search(self.name),
#                 cleanup_for_search(self.about),
#                 cleanup_for_search(self.headline)]
#        self.searchablecontent = "<br />".join(texts)
#        super(Person, self).save(*args, **kwargs)
