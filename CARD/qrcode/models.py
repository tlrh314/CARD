from django.db import models
from django.core.files import File
from django.core.files.base import ContentFile
from localsite.PyQRNative import *
from cStringIO import StringIO

class UrlQRCode(models.Model):
    url = models.URLField()
    qr_image = models.ImageField(
        upload_to="qr_codes/url/",
        height_field="qr_image_height",
        width_field="qr_image_width",
        null=True,
        blank=True,
        editable=False
    )
    qr_image_height = models.PositiveIntegerField(null=True, blank=True, \
            editable=False)
    qr_image_width = models.PositiveIntegerField(null=True, blank=True, \
            editable=False)
