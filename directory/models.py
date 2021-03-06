# -*- coding: utf-8 -*-
import datetime

from django.db import models
from django.utils.timezone import utc

# Object status
OBJECT_STATE_INVALID = -256
OBJECT_STATE_SYNC_ERROR = -1
OBJECT_STATE_SYNCED = 0
OBJECT_STATE_AWAITING_SYNC = 1
OBJECT_STATE_AWAITING_APPROVAL = 2
OBJECT_STATE_AWAITING_RECONCILIATION = 3
OBJECT_STATE_DELETED = 4
OBJECT_STATE_IMPORTED = 0

OBJECT_CHANGE_NOTHING_OBJECT = -1
OBJECT_CHANGE_CREATE_OBJECT = 0
OBJECT_CHANGE_UPDATE_OBJECT = 1
OBJECT_CHANGE_DELETE_OBJECT = 2

OBJECT_CHANGE_CREATE_ATTR = 3
OBJECT_CHANGE_UPDATE_ATTR = 4
OBJECT_CHANGE_DELETE_ATTR = 5

ATTRIBUTE_TYPE_FINAL = 0
ATTRIBUTE_TYPE_VIRTUAL = 1
ATTRIBUTE_TYPE_REFERENCE = 2

CHOICE_ATTRIBUT_TYPE = (
(0, "Final"),
(1, "Virtual"),
(2, "Reference")
)

CHOICE_ATTRIBUT_WIDGET = (
('forms.CharField', 'Text Field'),
('forms.IntegerField', 'Integer Field'),
('forms.DateField', 'Date Field'),
('forms.ChoiceField', 'Choice Field'),
)

# Reconciliation:
# Variable used for setting if the Object is deleted into the Target or
# if we need to add it to the Backend:
OBJECT_ADD_BACKEND = 0
OBJECT_DELETE_TARGET = 1
CHOICE_RECONCILIATION_OBJECT_MISSING_POLICY = (
(OBJECT_ADD_BACKEND, "ADD TO BACKEND"),
(OBJECT_DELETE_TARGET, "DELETE FROM TARGET")
)

# Variable enables to set which server, we need to upgrade values:
# If the value is TARGET, then the Backend object will replace the
# Target object
# else, the opposite.
TARGET = 0
BACKEND = 1
CHOICE_RECONCILIATION_OBJECT_DIFFERENT_POLICY = (
(TARGET, "TARGET"),
(BACKEND, "BACKEND")
)


class LBEAttribute(models.Model):
    displayName = models.CharField(unique=True, max_length=64)
    name = models.CharField(unique=True, max_length=64)
    regex = models.CharField(max_length=64, default='', blank=True)
    errorMessage = models.CharField(max_length=64, blank=True)

    def __unicode__(self):
        return str(self.displayName + ":" + self.name)


class LBEScript(models.Model):
    name = models.CharField(max_length=64)
    file = models.CharField(max_length=64)
    fileUpload = models.FileField(upload_to='custom')

    def __unicode__(self):
        return str(self.name)

# Use lbeobject.lbeattributeinstance_set.all() to get all attributes instance for a LBEObject
class LBEObjectTemplate(models.Model):
    name = models.CharField(unique=True, max_length=32)
    displayName = models.CharField(unique=True, max_length=32)
    # when change the RDN:
    instanceNameBeforeAttribute = models.ForeignKey(LBEAttribute, related_name='instance_name_before_attribute',
                                                    null=True, blank=True, default=None)
    # Used as name for an objectInstance
    instanceNameAttribute = models.ForeignKey(LBEAttribute, related_name='instance_name_attribute')
    # Used as displayName for an objectInstance
    instanceDisplayNameAttribute = models.ForeignKey(LBEAttribute, related_name='instance_displayname_attribute')
    # If > 0, this object need approvals. Must be positive
    approval = models.SmallIntegerField(default=0)
    # To increment each time an object is changed
    version = models.SmallIntegerField(default=0)
    # Every template must be associated to a class provided by the administrator
    script = models.ForeignKey(LBEScript, default=1)
    # Date of last import. Used to detect new objects in target by searching on createTimestamp (for LDAP) > last import
    imported_at = models.DateTimeField(default=datetime.datetime.fromtimestamp(0, utc))
    # Date of last sync
    synced_at = models.DateTimeField(default=datetime.datetime.fromtimestamp(0, utc))
    # Check if need to use Reconciliation for new RDN:
    needReconciliationRDN = models.BooleanField(default=False)
    # Reconciliation Policy:
    reconciliation_object_missing_policy = models.IntegerField(default=0,
                                                               choices=CHOICE_RECONCILIATION_OBJECT_MISSING_POLICY)
    reconciliation_object_different_policy = models.IntegerField(default=0,
                                                                 choices=CHOICE_RECONCILIATION_OBJECT_DIFFERENT_POLICY)

    def __unicode__(self):
        return str(self.displayName)


class LBEReference(models.Model):
    name = models.CharField(max_length=24)
    objectTemplate = models.ForeignKey(LBEObjectTemplate)
    objectAttribute = models.ForeignKey(LBEAttribute)

    def __unicode__(self):
        return str(self.name)


class LBEAttributeInstance(models.Model):
    lbeAttribute = models.ForeignKey(LBEAttribute)
    lbeObjectTemplate = models.ForeignKey(LBEObjectTemplate)
    defaultValue = models.CharField(max_length=64, default='', blank=True, null=True)
    mandatory = models.BooleanField(default=False)
    multivalue = models.BooleanField(default=True)
    position = models.IntegerField(default=1)
    reference = models.ForeignKey(LBEReference, null=True, blank=True, default=None)
    # If true, this attribute will be stored enciphered (by a symmetric key defined in LBE/settings.py) TODO: implement
    secure = models.BooleanField(default=False)
    unique = models.BooleanField(default=False)
    attributeType = models.SmallIntegerField(choices=CHOICE_ATTRIBUT_TYPE, default=ATTRIBUTE_TYPE_FINAL)
    # The HTML widget used to display/edit attribute. We'll inject classname
    widget = models.CharField(max_length=64, default='forms.CharField', choices=CHOICE_ATTRIBUT_WIDGET)
    widgetArgs = models.CharField(max_length=255, default='None')

    def __unicode__(self):
        return str(self.lbeObjectTemplate.name + ':' + self.lbeAttribute.name)


class LBEGroup(models.Model):
    name = models.CharField(default='groups', max_length=10)
    displayName = models.CharField(max_length=25, blank=False,unique=True)
    objectTemplate = models.ForeignKey(LBEObjectTemplate)
    version = models.SmallIntegerField(default=0)
    script = models.ForeignKey(LBEScript, default=1)
    imported_at = models.DateTimeField(default=datetime.datetime.fromtimestamp(0, utc))
    synced_at = models.DateTimeField(default=datetime.datetime.fromtimestamp(0, utc))
    approval = models.SmallIntegerField(default=0)
    instanceNameAttribute = models.ForeignKey(LBEAttribute, default=1) # 1= cn

    def __unicode__(self):
        return str(self.displayName)


class LBEDirectoryACL(models.Model):
    object = models.ForeignKey(LBEObjectTemplate, null=True, default=None, blank=True)
    group = models.ForeignKey(LBEGroup, null=True, default=None, blank=True)
    TYPE_CHOICE = (
    ('select', 'Select'), ('create', 'Create'), ('update', 'Update'), ('approval', 'Approval'), ('delete', 'Delete'))
    type = models.CharField(max_length=10, choices=TYPE_CHOICE, default="select")
    attribut = models.ForeignKey(LBEAttributeInstance, default=None, null=True)
    condition = models.CharField(max_length=100)

class log(models.Model):
    type = models.CharField(max_length=32)
    level = models.CharField(max_length=24)
    message = models.TextField()
    date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return str(self.level + ': ' + self.message)


# Fake model class, doesn't exists in the database. Used for abstraction
class LBEObjectInstance(object):
    def __init__(self, lbeObjectTemplate, *args, **kwargs):
        # List of fields (useful for completion too)
        self.template = lbeObjectTemplate
        self.attributes = {}
        self.status = OBJECT_STATE_INVALID
        now = datetime.datetime.now(utc)
        self.created_at = now
        self.updated_at = now
        self.synced_at = datetime.datetime.fromtimestamp(0, utc)
        # TODO: document usage  of changes
        self.changes = {
            'type': -1,
            'set': {},
        }
        self.name = None
        self.displayName = None

        if not kwargs == {}:
            for key, value in kwargs.iteritems():
                setattr(self, key, value)
        else:
            for key, value in args[1].iteritems():
                setattr(self, key, value)


    def __unicode__(self):
        return 'name: ' + self.name + ', displayName: ' + self.displayName + ', attributes: ' + self.attributes

    def toDict(self):
        return {'_id': self.name,
                'attributes': self.attributes,
                'displayName': self.displayName,
                'status': self.status,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'synced_at': self.synced_at,
                'changes': {'type': self.changes['type'], 'set': self.changes['set']},
        }


# Fake class too
class LBEGroupInstance(LBEObjectInstance):
    def __init__(self, lbeGroupTemplate, *args, **kwargs):
        super(LBEGroupInstance, self).__init__(lbeGroupTemplate, args, kwargs)
        self.name = self.template.displayName
        self.displayName = self.template.displayName

    def __unicode__(self):
        return 'name: ' + self.template.name