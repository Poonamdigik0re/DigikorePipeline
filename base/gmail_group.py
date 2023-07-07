import json
import traceback

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from base.models import GmailGroup
from utils.celery import error_log, create_gmail_group, update_gmail_group_members


@permission_required('base.gmail_group')
def home(request):
    return render(request, 'gmail_group.html')


@permission_required('base.gmail_group')
def get_all_groups(request):
    try:
        groups = list(GmailGroup.objects.values('id', 'name', 'email', 'created_on', ))
        members = list(
            GmailGroup.objects.values('id', 'members__id', 'members__userprofile__full_name', 'members__email'))

        for group in groups:
            group['members'] = [x for x in members if x['id'] == group['id']]

        return JsonResponse(groups, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.gmail_group')
def get_all_users(request):
    try:
        data = list(User.objects.filter(is_active=True).values('id', 'userprofile__full_name', 'email'))

        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.create_gmail_group')
def create_group(request):
    try:
        data = json.loads(request.body)

        if not data['group_id']:
            gmail_group = GmailGroup(name=data['name'], email=data['email'])
            gmail_group.save()
            # add users after creating the gmail group
            gmail_group.members.set(data['members'])

            create_gmail_group.delay(gmail_group.id)
        else:
            gmail_group = GmailGroup.objects.get(id=data['group_id'])
            gmail_group.members.set(data['members'])
            gmail_group.save()

            update_gmail_group_members.delay(gmail_group.id)

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
