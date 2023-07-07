import datetime
import json
import traceback

from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

# from DigikorePortal.settings import MODELS
# from base.models import Ticket, Note, UserProfile, NoteType, TicketStatus, TicketType, TicketPriority, User
# from utils.celery import error_log, wss_publish


def home(request):
    return render(request, 'uploadfile.html')


# @permission_required('base.tickets')
# def get_defaults(request):
#     try:
#         data = {
#             'priority': list(TicketPriority.objects.values('id', 'name', 'default', 'order')),
#             'status': list(TicketStatus.objects.values('id', 'name', 'default', 'order')),
#             'type': list(TicketType.objects.values('id', 'name', 'default', 'order')),
#         }

#         if request.user.has_perm('base.tickets_admin'):
#             data['users'] = list(User.objects.filter(is_active=True).values('id', 'userprofile__full_name').order_by(
#                 'userprofile__full_name'))
#         elif request.user.has_perm('base.tickets_maintainer'):
#             data['users'] = list(User.objects.filter(id=request.user.id).values('id', 'userprofile__full_name'))
#         else:
#             data['users'] = []

#         return JsonResponse(data, safe=True)

#     except Exception as error:
#         error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
#         return HttpResponseBadRequest(error)


# @permission_required('base.tickets')
# def get_all_tickets(request):
#     try:
#         data = json.loads(request.body)

#         filters = {}
#         if data['ticket_id']:
#             filters['id'] = data['ticket_id']

#         if request.user.has_perm('base.tickets_admin') or request.user.has_perm('base.tickets_maintainer'):
#             pass
#         else:
#             filters['created_by'] = request.user

#         data = list(Ticket.objects.filter(**filters).values(*MODELS['default']['ticket']))

#         return JsonResponse(data, safe=False)

#     except Exception as error:
#         error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
#         return HttpResponseBadRequest(error)


# @permission_required('base.tickets')
# def add_ticket(request):
#     try:
#         data = json.loads(request.body)

#         default_status = TicketStatus.objects.get(default=True)

#         ticket = Ticket(title=data['title'], description=data['description'], type_id=data['type_id'],
#                         priority_id=data['priority_id'], status=default_status, created_by=request.user)
#         ticket.save()
#         resp = {'id': ticket.id}

#         wss_publish.delay('tickets', {'func': 'wss_ticket_created', 'data': resp})

#         return JsonResponse(resp, safe=False)

#     except Exception as error:
#         error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
#         return HttpResponseBadRequest(error)


# @permission_required('base.tickets')
# def ticket_home(request, ticket_id):
#     return render(request, 'update_tickets.html')


# @permission_required('base.tickets')
# def get_ticket_details(request, ticket_id):
#     try:
#         ticket = list(Ticket.objects.filter(id=ticket_id).values(*MODELS['default']['ticket']))

#         return JsonResponse(ticket, safe=False)

#     except Exception as error:
#         error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
#         return HttpResponseBadRequest(error)


# @permission_required('base.tickets')
# def add_note(request, ticket_id):
#     try:
#         data = json.loads(request.body)
#         parent_type = 'ticket'
#         parent_id = ticket_id
#         text = data['note_text']
#         note_type = NoteType.objects.get(default=True)

#         note = Note(parent_id=parent_id, parent_type=parent_type, text=text, type=note_type, created_by=request.user)
#         note.save()

#         resp = list(Note.objects.filter(id=note.id).values(*MODELS['default']['note']))

#         return JsonResponse(resp, safe=False)

#     except Exception as error:
#         error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
#         return HttpResponseBadRequest(error)


# @login_required
# def get_notes(request, ticket_id):
#     try:
#         parent_type = 'ticket'
#         parent_id = ticket_id

#         resp = list(Note.objects.filter(parent_type=parent_type, parent_id=parent_id).values(
#             *MODELS['default']['note']).order_by('-type__order', '-id'))

#         return JsonResponse(resp, safe=False)

#     except Exception as error:
#         error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
#         return HttpResponseBadRequest(error)


# @permission_required('base.tickets')
# def update_ticket(request, ticket_id):
#     try:
#         data = json.loads(request.body)
#         ticket = Ticket.objects.get(id=ticket_id)

#         assert not ticket.status.locked, "This ticket is locked, you can not change the status of this ticket."

#         for k, v in data.items():
#             if hasattr(ticket, k) and v:
#                 if str(getattr(ticket, k)) != v:
#                     if k == 'status_id':
#                         old_value = ticket.status.name
#                         new_value = TicketStatus.objects.get(id=v).name
#                         if new_value == 'Resolved':
#                             ticket.resolved_by_id = request.user
#                             ticket.resolved_on = datetime.datetime.now()
#                         text = f'Ticket Status has been changed from {old_value} to {new_value}.'

#                     elif k == 'priority_id':
#                         old_value = ticket.priority.name
#                         new_value = TicketPriority.objects.get(id=v).name
#                         text = f'Ticket Priority has been changed from {old_value} to {new_value}.'

#                     elif k == 'type_id':
#                         old_value = ticket.type.name
#                         new_value = TicketType.objects.get(id=v).name
#                         text = f'Ticket Type has been changed from {old_value} to {new_value}.'

#                     elif k == 'assigned_to_id':
#                         old_value = ticket.assigned_to.userprofile.full_name if ticket.assigned_to else None
#                         new_value = UserProfile.objects.get(user_id=v).full_name
#                         ticket.assigned_on = datetime.datetime.now()
#                         text = f'Ticket Assignment has been changed from {old_value} to {new_value}.'
#                     else:
#                         continue

#                     setattr(ticket, k, v)
#                     ticket.save()

#                     Note(parent_type='ticket', parent_id=ticket.id, text=text, created_by=request.user,
#                          type=NoteType.objects.get(default=True)).save()

#                     wss_publish.delay(f'tickets{ticket_id}', {
#                         'func': 'wss_ticket_updated', 'data': {'key': k, 'value': v}})

#         return HttpResponse()

#     except Exception as error:
#         error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
#         return HttpResponseBadRequest(error)
