import csv
import traceback

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render

from base.models import UserProfile
from utils.celery import error_log


@permission_required('base.transportation_page')
def home(request):
    return render(request, 'transportation.html')


@permission_required('base.transportation_page')
def get_employees(request):
    try:
        values = ('empid', 'full_name', 'team__shift__intime', 'department__name', 'designation__name', 'gender',
                  'phone', 'current_address', 'permanent_address', 'emergency_contact', 'emergency_phone')
        resp = list(UserProfile.objects.filter(user__is_active=True, transport_required='yes').values(*values).order_by(
            'team__shift__intime'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.transportation_page')
def download_as_csv(request):
    try:
        response = HttpResponse(content_type='text/csv')
        response[
            'Content-Disposition'] = 'attachment; filename="Transportation_List.csv"'

        writer = csv.writer(response)
        writer.writerow(['EMPID', 'Name', 'Shift Time', 'Department', 'Gender', 'Phone', 'Current Address',
                         'Permanent Address', 'Emergency Contact', 'Emergency Phone'])

        values = ('empid', 'full_name', 'team__shift__intime', 'department__name', 'gender',
                  'phone', 'current_address', 'permanent_address', 'emergency_contact', 'emergency_phone')

        employees = list(UserProfile.objects.filter(
            user__is_active=True, transport_required='yes').values_list(*values).order_by('team__shift__intime'))

        for emp in employees:
            writer.writerow(emp)

        return response

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
