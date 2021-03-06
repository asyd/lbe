from django.core.management.base import BaseCommand
import django

from services.backend import BackendHelper
from services.target import TargetHelper
from directory.models import LBEObjectTemplate, LBEGroup

from services.group import GroupInstanceHelper
from services.object import LBEObjectInstanceHelper


class ImportTarget():
    def __init__(self):
        self.backend = BackendHelper()
        self.target = TargetHelper()
        self.start_date = django.utils.timezone.now()

    def _getID(self, listRDN):
        listID = []
        for rdn in listRDN:
            listID.append(rdn.split('=')[1].split(',')[0])
        return listID

    def save(self):
        print 'Checking for Objects which do not exist into LBE Backend but in LDAP Server:'
        for objectTemplate in LBEObjectTemplate.objects.all():
            objectHelper = LBEObjectInstanceHelper(objectTemplate)
            try:
                scope = objectHelper.callScriptClassMethod("search_scope")
            except BaseException:
                scope = 0
            filter = '(&'
            for oc in objectHelper.callScriptClassMethod('object_classes'):
                filter += '(objectClass=' + oc + ')'
            filter += ')'
            print '\033[91m' + objectTemplate.name + '\033[0m: (\033[95m' + objectHelper.callScriptClassMethod("base_dn") + '\033[0m) using \033[95m' + filter + '\033[0m'
            objTarget = self.target.searchObjects(objectTemplate, scope)
            objBackend = self.backend.searchObjects(objectTemplate)
            number = 0
            for ot in objTarget:
                exist = False
                for ob in objBackend:
                    if ot.name == ob.name:
                        exist = True
                        break
                if not exist:
                    number += 1
                    print '=> Adding \033[95m' + ot.name + '\033[0m object into LBE Backend... '
                    print " values: " + str(ot.attributes)
                    try:
                        self.backend.createObject(objectTemplate, ot, True)
                        print "\033[92mDone.\033[0m\n"
                    except BaseException as e:
                        print "\033[91mFail.\033[0m"
                        print "''''''''"
                        print e
                        print "''''''''"
            if number == 0:
                print '<None>'
            # Synced object:
            objectTemplate.synced_at = django.utils.timezone.now()
            objectTemplate.save()
        print '.........................'
        print 'Checking for Groups which do not exist into LBE Backend but in Target:'
        for groupTemplate in LBEGroup.objects.all():
            groupInstance = GroupInstanceHelper(groupTemplate)
            try:
                scope = groupInstance.callScriptClassMethod("search_scope")
            except BaseException:
                scope = 0
            grpTarget = self.target.searchObjects(groupTemplate, scope)
            grpBackend = self.backend.searchObjects(groupTemplate)
            for gt in grpTarget:
                exist = False
                for gb in grpBackend:
                    if gt.name == gb.name:
                        exist = True
                        break
                if not exist:
                    # import only existing group into LBE config
                    try:
                        LBEGroup.objects.get(displayName__iexact=gt.displayName)
                    except BaseException:
                        continue
                    print '=> Adding \033[95m' + gt.name + '\033[0m group into LBE Backend... '
                    print " values: " + str(gt.attributes)
                    try:
                        if groupInstance.attributeName in gt.attributes:
                            gt.attributes[groupInstance.attributeName] = self._getID(gt.attributes[groupInstance.attributeName])
                        groupHelper = GroupInstanceHelper(groupTemplate, gt)
                        groupHelper.createTemplate(True)
                            #print " >\033[91mThis group does not exists in LBE Configuration Group.\033[0m"
                            #print " >\033[91mIn order to see, manage it, please create it using some extra attribute:"
                            #print "  >\033[91m'Display Name': \033[95m" + gt.name + "\033[0m"
                            #print " >\033[91mInto the Script file:"
                            #print "  >'DN Attribute': \033[95m" + groupHelper.callScriptClassMethod("base_dn") + "\033[91m"
                            #print "  >'Attribute Name' & 'Object Classes': as you wish.\033[0m"
                        print "\033[92mDone.\033[0m\n"
                    except BaseException as e:
                        print "\033[91mFail.\033[0m\n"
                        print "''''''''"
                        print e
                        print "''''''''"
            # Synced group:
            groupTemplate.synced_at = django.utils.timezone.now()
            groupTemplate.save()
        print "End."


class Command(BaseCommand):
    def handle(self, *args, **options):
        importTarget = ImportTarget()
        importTarget.save()
