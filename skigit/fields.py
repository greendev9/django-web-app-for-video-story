import math
import operator
from django.conf import settings
from django import forms
from django.db import models
from django.db.models.fields import files

from skigit.storage import B2Storage

from user.models import Profile
from django.contrib.auth.models import User


class B2FieldFile(files.FieldFile):
	def get_meta(self):
		return self.storage.get_meta(self.name)
	meta = property(get_meta)


class B2Field(models.FileField):
	"""
	Model field for Backblaze B2 storage. Descendant of
	:py:class:`django.db.models.FileField`.
	"""
	attr_class = B2FieldFile

	def __init__(self, *args, **kwargs):
		defaults = {'storage': B2Storage()}
		defaults.update(kwargs)
		super(B2Field, self).__init__(*args, **defaults)

	def formfield(self, **kwargs):
		defaults = {'form_class': B2FormField}
		defaults.update(kwargs)
		return super(B2Field, self).formfield(**defaults)

	def deconstruct(self):
		name, path, args, kwargs = super(B2Field, self).deconstruct()
		return name, path, args, kwargs

	def south_field_triple(self):
		name, path, args, kwargs = self.deconstruct()
		return '{}.{}'.format(path, name), args, kwargs


class B2FormField(forms.FileField):
	"""
	Form field for Backblaze B2 storage. Descendant of
	:py:class:`django.forms.FileField`
	"""
	pass


class BusinessProfileNameField(forms.ModelChoiceField):
	"""
	Show business profile name for the user!
	"""
	def label_from_instance(self, obj):

		return obj.profile.company_title