import json
import traceback

from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from base.models import Client, Project, Contact
from utils.celery import create_client_signiant_folder, error_log


@permission_required('base.clients_list')
def home(request):
    return render(request, 'clients_list.html')


@permission_required('base.clients_list')
def get_all_clients(request):
    try:
        clients = list(Client.objects.values('id', 'name', 'address').order_by('name'))

        return JsonResponse(clients, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.clients_list')
def get_all_projects(request):
    try:
        data = json.loads(request.body)
        client_id = data['client_id']

        projects = list(Project.objects.filter(client_id=client_id).values('id', 'name', 'type__name', 'status__name'))

        return JsonResponse(projects, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.clients_list')
def get_all_contacts(request):
    try:
        data = json.loads(request.body)
        client_id = data['client_id']

        client = Client.objects.get(id=client_id)
        contacts = []

        if client.contacts.count() > 0:
            contacts = list(client.contacts.values('id', 'name', 'email', 'phone', 'title'))

        return JsonResponse(contacts, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.clients_list')
def add_new_client(request):
    try:
        data = json.loads(request.body)

        client_id = data.get('id', None)

        if client_id:
            client = Client.objects.get(id=client_id)
            client.name = data['name']
            client.address = data['address']
            client.save()
        else:
            client = Client(name=data['name'], address=data['address'], created_by=request.user)
            client.save()

            # create the signiant folder
            create_client_signiant_folder.delay(data['name'])

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.clients_list')
def add_new_contact(request):
    try:
        data = json.loads(request.body)
        contact_id = data['id']

        if contact_id:
            contact = Contact.objects.get(id=contact_id)

            contact.name = data['name'].strip()
            contact.email = data['email'].strip()
            contact.title = data['title'].strip()
            contact.phone = data['phone'].strip()
            contact.save()

        else:
            contact = Contact(name=data['name'].strip(), email=data['email'].strip(),
                              title=data['title'].strip(), phone=data['phone'].strip(), created_by=request.user)
            contact.save()

        client = Client.objects.get(id=data['client_id'])
        client.contacts.add(contact)

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
