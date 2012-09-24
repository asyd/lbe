# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, redirect
from django.http import HttpResponse
from directory.models import *
from directory.forms import *
from services.object import LBEObjectInstanceHelper
from django.template import RequestContext
from services.backend import BackendHelper, BackendObjectAlreadyExist
from django.contrib import messages

def index(request):
    backend = BackendHelper()
    objects = backend.searchObjects(LBEObjectTemplate.objects.get(name='employee'))
    lbeObject = LBEObjectTemplate.objects.get(name__iexact="employee")
    return render_to_response('directory/default/index.html', { 'objects': objects,'lbeObjectId': lbeObject.id }, context_instance=RequestContext(request))

# Create an instance of LBEObjectInstance from LBEObject definition. Save it into MongoDB with status AWAITING_SYNC
def addObjectInstance(request, lbeObject_id = None):
    form = None
    if request.method == 'POST':
        form = LBEObjectInstanceForm(LBEObjectTemplate.objects.get(id = lbeObject_id), request.POST)
        helper = LBEObjectInstanceHelper(LBEObjectTemplate.objects.get(id = lbeObject_id))
        if form.is_valid():
            helper.createFromDict(request)
            try:
                helper.save()
            except BackendObjectAlreadyExist as e:
                messages.add_message(request, messages.ERROR, 'Object already exists')
                return render_to_response('directory/default/object/add.html', { 'form': form, 'lbeObjectId': lbeObject_id }, context_instance=RequestContext(request))
            # Redirect to list
            return redirect('/directory/')
        else:
            render_to_response('directory/default/object/add.html', { 'form': form, 'lbeObjectId': lbeObject_id }, context_instance=RequestContext(request))
        return render_to_response('directory/default/object/add.html', { 'form': form, 'lbeObjectId': lbeObject_id }, context_instance=RequestContext(request))
    else:
        if lbeObject_id is None:
            # TODO: Redirect to a form to choose which object to add
            print 'error'
    form = LBEObjectInstanceForm(LBEObjectTemplate.objects.get(id = lbeObject_id))
    return render_to_response('directory/default/object/add.html', { 'form': form, 'lbeObjectId': lbeObject_id }, context_instance=RequestContext(request))

#@manage_acl()    
def manageObjectInstance(request, obj_id,uid,type):
	if request.is_ajax():
		nb = 0
		if type == 'modify':
			html = '<input type="text" name="'+ request.GET.keys()[nb] +'" id="'+request.GET.keys()[nb]+'" value="'+request.GET[request.GET.keys()[nb]]+'" onBlur="save(\'/directory/object/manage/'+obj_id+'/'+uid+'\',\''+request.GET.keys()[nb]+'\',$(\'#'+request.GET.keys()[nb]+'\').val());"/>'
		elif type == 'save':
			html = request.GET[request.GET.keys()[nb]]
			# save value (replace):
			helper = LBEObjectInstanceHelper(LBEObjectTemplate.objects.get(id = obj_id))
			helper.updateFromDict(uid,request.GET)
			helper.modify()
		# elif type == 'add':
			# TODO
		return HttpResponse(html)
	backend = BackendHelper()
	objectValue = backend.getObjectByName(LBEObjectTemplate.objects.get(id=obj_id),uniqueName=uid)
	return render_to_response('directory/default/object/manage.html',{'object':objectValue,'lbeObjectId':obj_id},context_instance=RequestContext(request))

#@manage_acl('modify')
def modifyObjectInstance(request,obj_id,uid):
	return HttpResponse('coucou')
