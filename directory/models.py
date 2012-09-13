# -*- coding: utf-8 -*-
from django.db import models
from django import forms

# Object status
OBJECT_STATE_INVALID = -256
OBJECT_STATE_SYNC_ERROR = -1
OBJECT_STATE_SYNCED = 0
OBJECT_STATE_AWAITING_SYNC = 1
OBJECT_STATE_AWAITING_APPROVAL = 2
OBJECT_STATE_IMPORTED = 1

OBJECT_TYPE_FINAL = 0
OBJECT_TYPE_VIRTUAL = 1
OBJECT_TYPE_REFERENCE = 2

class LBEAttribute(models.Model):
	displayName       = models.CharField(unique = True, max_length=64)
	name         	  = models.CharField(unique = True, max_length=64)
	# some fields (like syntax, max size) will be added later
	def __unicode__(self):
		return str(self.displayName + ":" + self.name)

class LBEObjectClass(models.Model):
	name        	  = models.CharField(unique = True, max_length=64)
	def __unicode__(self):
		return str(self.name)

class LBEScript(models.Model):
	name      = models.CharField(max_length=64)
	file      = models.FileField(upload_to='script')
	# TODO: Probablement à supprimer, juste avoir une référence vers le nom du fichier
	#value     = models.CharField(max_length=64)
	#tab       = models.CharField(max_length=64)
	def __unicode__(self):
		return str(self.name)

# Use lbeobject.lbeattributeinstance_set.all() to get all attributes instance for a LBEObject
class LBEObjectTemplate(models.Model):
	displayName  	  = models.CharField(unique = True, max_length=32)
	name         	  = models.CharField(unique = True, max_length=32)
	baseDN       	  = models.CharField(max_length=256)
	uniqueAttribute  	  = models.ForeignKey(LBEAttribute, related_name = 'unique_attribute')
	approval		  = models.SmallIntegerField(default = 0) # If > 0, this object need approvals. Must be positive
	objectClasses     = models.ManyToManyField(LBEObjectClass, null = True, default = None)
	# To increment each time an object is changed. TODO: add this field in backend
	version           = models.SmallIntegerField(default = 0)
	script         	  = models.ForeignKey(LBEScript, null = True, blank = True, default = None)
	def __unicode__(self):
		return str(self.displayName)

class LBEReference(models.Model):
	name              = models.CharField(max_length=24)

class LBEAttributeInstance(models.Model):
	lbeAttribute      = models.ForeignKey(LBEAttribute)
	lbeObjectTemplate = models.ForeignKey(LBEObjectTemplate)
	defaultValue      = models.CharField(max_length=64, default='', blank = True, null = True)
	mandatory         = models.BooleanField(default = False)
	multivalue        = models.BooleanField(default = True)
	reference         = models.ForeignKey(LBEReference, null = True, blank = True, default = None)
	# If true, this attribute will be stored enciphered (by a symmetric key defined in LBE/settings.py) TODO: implement
	secure		      = models.BooleanField(default = False)
	objectType        = models.SmallIntegerField(default = OBJECT_TYPE_FINAL)
	# The HTML widget used to display/edit attribute. We'll inject classname
	widget            = models.CharField(max_length=64, default = 'forms.CharField', blank = True)
	widgetArgs        = models.CharField(max_length=255, default = 'None')

class LBEDirectoryACL(models.Model):
	object = models.CharField(max_length=25) # TODO: Why it's not a foreign key?
	type = models.CharField(max_length=10) # TODO: DOCUMENT probably use constants
	attribut = models.CharField(max_length=35) # TODO: Why it's not a foreign key?
	condition = models.CharField(max_length=100)

# Fake model class, doesn't exists in the database. Used for abstraction
class LBEObjectInstance:
	def __init__(self, dn, object_type, name, attributes = {}):
		self.dn = dn
		self.objectType = object_type
		self.displayName = name
		# Attributes will be stored a { cn: ['Bruno Bonfils'], mail: [ 'bruno@opencsi.com', 'bbonfils@opencsi.com' ] }
		# IMPORTANT: Even mono valued fields are store in a list !
		self.attributes = attributes
		self.status = OBJECT_STATE_INVALID

	def add_attribute(self, name, values):
		self.attributes[name] = values
	
	def set_status(self, status):
		self.status = status
	
	# TODO: implement
	def is_valid(self):
		pass
	
	def search(self, filter):
		pass
		
	def save(self):
		pass
