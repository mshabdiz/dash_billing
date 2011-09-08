# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Fourth Paradigm Development, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Views for managing Nova instances.
"""
import datetime
import logging

from django import http
from django import shortcuts
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from django_openstack import api
from django_openstack import forms
from django_openstack import utils
from django_openstack.models import AccountRecord
from django_openstack.decorators import enforce_admin_access

import openstack.compute.servers
import openstackx.api.exceptions as api_exceptions

LOG = logging.getLogger('django_openstack.dash')

class CreateAccountRecord(forms.SelfHandlingForm):
    tenant_id = forms.CharField(max_length="100", label="Tenant ID")
    amount = forms.DecimalField(label="Amount")
    memo = forms.CharField(max_length="300", label="Memo")

    def handle(self, request, data):
        accountRecord = AccountRecord(tenant_id=data['tenant_id'],amount=int(data['amount']),memo=data['memo'])
        accountRecord.save()
        msg = '%s was successfully added to .' % data['tenant_id']
        LOG.info(msg)
        messages.success(request, msg)
        return shortcuts.redirect('syspanel_billing')


class DeleteAccountRecord(forms.SelfHandlingForm):
    id = forms.CharField(required=True)

    def handle(self, request, data):
        try:
            id = data['id']
            print "id %s" % id
            LOG.info('Deleting account with id "%s"' % id)
            accountRecord = AccountRecord.objects.get(id=id)
            print "delete %r" % accountRecord
            accountRecord.delete()

            messages.info(request, 'Successfully deleted record: %s' %
                          id)
        except api_exceptions.ApiException, e:
            messages.error(request, 'Unable to delete recode: %s' %
                                     e.message)
        return shortcuts.redirect(request.build_absolute_uri())


@login_required
@enforce_admin_access
def index(request):
    print "piyo: billing index"
    for f in (DeleteAccountRecord,):
        _, handled = f.maybe_handle(request)
        if handled:
            return handled
    print "############################"
    delete_form = DeleteAccountRecord()
    print "request.user.service_catalog %s" % request.user.service_catalog

    account_record_list = AccountRecord.objects.all()
    return shortcuts.render_to_response('syspanel_billing.html', 
    {'account_record_list':account_record_list, 'delete_form': delete_form}, context_instance=template.RequestContext(request))

@login_required
@enforce_admin_access
def create(request):
    form, handled = CreateAccountRecord.maybe_handle(request)
    if handled:
        return handled
    return shortcuts.render_to_response('syspanel_create_account.html',{
        'form': form,
    }, context_instance = template.RequestContext(request))

