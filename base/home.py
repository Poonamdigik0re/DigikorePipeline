import datetime
import json
import traceback

from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from base.models import UserProfile, Announcement
from utils.celery import error_log


@login_required
def home(request):
    return render(request, 'home.html')


@cache_page(60 * 60 * 24)
@login_required
def get_upcoming_birthdays(request):
    try:
        today = datetime.date.today()

        birthdays = []
        filters = {'user__is_active': True, 'date_of_birth__month': today.month, 'date_of_birth__day__gte': today.day}
        values = ('date_of_birth', 'full_name')

        for user in UserProfile.objects.filter(**filters).order_by('date_of_birth__day').values(*values):
            birthdays.append({'day': user['date_of_birth'].strftime('%b %d'), 'name': user['full_name']})

        return JsonResponse(birthdays, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@login_required
def get_announcements(request):
    try:
        today = datetime.date.today() - datetime.timedelta(days=1)
        data = list(Announcement.objects.filter(valid_till__gte=today).values('text').order_by('-id'))

        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.add_announcement')
def add_announcement(request):
    try:
        data = json.loads(request.body)

        Announcement(text=data['text'], valid_till=data['valid_till'], created_by=request.user).save()

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
