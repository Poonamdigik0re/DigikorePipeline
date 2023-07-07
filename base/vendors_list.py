import json
import traceback

from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from base.models import Vendor, Project, Contact
from utils.celery import error_log


@permission_required('base.vendors_list')
def home(request):
    return render(request, 'vendors_list.html')


@permission_required('base.vendors_list')
def get_all_vendors(request):
    try:
        vendors = list(Vendor.objects.values('id', 'name', 'address').order_by('name'))

        return JsonResponse(vendors, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.vendors_list')
def get_all_projects(request):
    try:
        data = json.loads(request.body)
        vendor_id = data['vendor_id']

        projects = list(Project.objects.filter(vendors=vendor_id).values('id', 'name', 'type__name', 'status__name'))

        return JsonResponse(projects, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.vendors_list')
def get_all_contacts(request):
    try:
        data = json.loads(request.body)
        vendor_id = data['vendor_id']

        vendor = Vendor.objects.get(id=vendor_id)
        contacts = []

        if vendor.contacts.count() > 0:
            contacts = list(vendor.contacts.values('id', 'name', 'email', 'phone', 'title'))

        return JsonResponse(contacts, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.vendors_list')
def add_new_vendor(request):
    try:
        data = json.loads(request.body)

        vendor = Vendor(name=data['name'], address=data['address'], created_by=request.user)
        vendor.save()

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.vendors_list')
def add_new_contact(request):
    try:
        data = json.loads(request.body)

        contact = Contact(name=data['name'].strip(), email=data['email'].strip(),
                          title=data['title'].strip(), phone=data['phone'].strip(), created_by=request.user)
        contact.save()

        vendor = Vendor.objects.get(id=data['vendor_id'])
        vendor.contacts.add(contact)

        resp = {
            'contacts__id': contact.id,
            'contacts__name': contact.name,
            'contacts__email': contact.email,
            'contacts__phone': contact.phone,
            'contacts__title': contact.title
        }

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
