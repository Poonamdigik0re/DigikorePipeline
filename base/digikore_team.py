import traceback

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render

from base.models import UserProfile
from utils.celery import error_log


@login_required
def home(request):
    return render(request, 'digikore_team.html')


@login_required
def get_all_employees(request):
    try:
        data = list(UserProfile.objects.filter(user__is_active=True).order_by('id').values(
            'location_id', 'full_name', 'department_id', 'department__name', 'designation_id', 'designation__name',
            'profile_picture'
        ))

        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
