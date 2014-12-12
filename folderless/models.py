# coding: utf-8

from __future__ import unicode_literals
import hashlib
import os

from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from django.core import urlresolvers
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from easy_thumbnails.fields import ThumbnailerField
from easy_thumbnails.files import get_thumbnailer

from conf import settings

OTHER_TYPE = 'other'


@python_2_unicode_compatible
class File(models.Model):
    file = ThumbnailerField(
        _('File'), upload_to=settings.FOLDERLESS_UPLOAD_TO,
        storage=settings.FOLDERLESS_FILE_STORAGE,
        thumbnail_storage=settings.FOLDERLESS_THUMBNAIL_STORAGE)
    name = models.CharField(
        _('name'), max_length=255, blank=True, default='')
    filename = models.CharField(
        _('Filename'),
        help_text=_(u'Use for renaming your file on the server'),
        max_length=255, blank=False, unique=True)
    author = models.CharField(
        _('Author'), max_length=255, blank=True, default='')
    copyright = models.CharField(
        _('Copyright'), max_length=255, blank=True, default='')
    type = models.CharField(
        _('File type'), max_length=12, choices=(), blank=True)
    uploader = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        related_name='owned_files', null=True, blank=True,
        verbose_name=_('Uploader'))
    created = models.DateTimeField(
        _('Created'), default=timezone.now)
    modified = models.DateTimeField(
        _('Modified'), auto_now=True)
    extension = models.CharField(
        _('Extension'), max_length=255, blank=True, default='')
    file_hash = models.CharField(
        _('Checksum'), help_text=_(u'For preventing duplicates'),
        max_length=40, blank=False, unique=True)

    def __str__(self):
        return '%s' % self.filename

    class Meta:
        verbose_name = _(u'File')
        verbose_name_plural = _(u'Files')

    def save(self, *args, **kwargs):
        if not self.filename:
            self.filename = self.file.file
        super(File, self).save(*args, **kwargs)

    def generate_file_hash(self):
        sha = hashlib.sha1()
        self.file.seek(0)
        while True:
            # digest size for sha1 is 160 bytes, so a multiple should do best.
            buf = self.file.read(160000)
            if not buf:
                break
            sha.update(buf)
        self.file_hash = sha.hexdigest()
        # to make sure later operations can read the whole file
        self.file.seek(0)

    @property
    def is_image(self):
        if self.file:
            image_definition = settings.FOLDERLESS_FILE_TYPES.get(
                'image', None)
            if image_definition is not None:
                if self.extension in image_definition.get('extensions'):
                    return True
        return False

    @property
    def label(self):
        if self.name:
            return '%s (%s)' % (self.name, self.filename)
        else:
            return self.filename

    @property
    def admin_url(self):
        return urlresolvers.reverse(
            'admin:folderless_file_change',
            args=(self.pk,)
        )

    @property
    def thumb_field_url(self):
        if self.is_image:
            return self._thumb_url(
                settings.FOLDERLESS_IMAGE_WIDTH_FIELD,
                settings.FOLDERLESS_IMAGE_HEIGHT_FIELD)
        else:
            return

    @property
    def thumb_list_url(self):
        if self.is_image:
            return self._thumb_url(
                settings.FOLDERLESS_IMAGE_WIDTH_LIST,
                settings.FOLDERLESS_IMAGE_HEIGHT_LIST)
        else:
            return

    def thumb_list(self):
        if self.is_image:
            url = self.thumb_list_url
            return '<a href="%s" target="_blank"><img src="%s" alt="%s"></a>' \
                   % (self.file.url, url, self.label)
        else:
            return

    thumb_list.allow_tags = True
    thumb_list.short_description = _(u'Thumb')

    def references_list(self):
        links = [
            rel.get_accessor_name()
            for rel in File._meta.get_all_related_objects()]
        total = 0
        for link in links:
            total += getattr(self, link).all().count()
        if total > 0:
            return "%sx" % total
        else:
            return "-"

    references_list.allow_tags = True
    references_list.short_description = _(u'Referenced?')

    def get_json_response(self):
        return {
            'id': self.id,
            'file_url': self.file.url,
            'edit_url': self.admin_url,
            'thumbnail_list': self.thumb_list_url,
            'thumbnail_field': self.thumb_field_url,
            'label': self.label,
        }

    def _thumb_url(self, width, height):
        thumbnailer = get_thumbnailer(self.file)
        thumbnail_options = {
            'size': (width, height)
        }
        thumb = thumbnailer.get_thumbnail(thumbnail_options)
        return thumb.url

    @property
    def url(self):
        """
        to make the model behave like a file field
        """
        try:
            r = self.file.url
        except:
            r = ''
        return r


@receiver(pre_save, sender=File, dispatch_uid="folderless_file_processing")
def folderless_file_processing(sender, **kwargs):
    instance = kwargs.get("instance")
    if instance.file:
        name, extension = os.path.splitext(instance.file.name)
        if len(extension) > 1:
            instance.extension = extension[1:].lower()
        else:
            instance.extension = ''
        instance.type = OTHER_TYPE
        for type, definition in settings.FOLDERLESS_FILE_TYPES.iteritems():
            if instance.extension in definition.get("extensions"):
                instance.type = type
        instance.generate_file_hash()


# do this with a signal, to catch them all
@receiver(pre_delete, sender=File)
def cleanup_file_on_delete(sender, instance, **kwargs):
    instance.file.delete(False)
