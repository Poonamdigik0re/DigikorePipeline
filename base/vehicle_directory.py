import csv
import traceback

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render

from base.models import UserProfile
from utils.celery import error_log


@permission_required('base.vehicle_directory')
def home(request):
    return render(request, 'vehicle_directory.html')


@permission_required('base.vehicle_directory')
def get_employees(request):
    try:
        values = ('empid', 'full_name', 'team__shift__intime', 'department__name', 'designation__name', 'gender',
                  'phone', 'vehicle_type', 'vehicle_number')
        resp = list(UserProfile.objects.filter(user__is_active=True,
                                               vehicle_number__isnull=False).values(*values).order_by(
            'team__shift__intime'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.vehicle_directory')
def download_as_csv(request):
    try:
        response = HttpResponse(content_type='text/csv')
        response[
            'Content-Disposition'] = 'attachment; filename="Vehicle_Directory.csv"'

        writer = csv.writer(response)
        writer.writerow(['EMPID', 'Name', 'Shift Time', 'Department', 'Gender', 'Phone',
                         'Vehicle Type', 'Vehicle Number'])

        values = ('empid', 'full_name', 'team__shift__intime', 'department__name', 'gender',
                  'phone', 'vehicle_type', 'vehicle_number')

        employees = list(UserProfile.objects.filter(
            user__is_active=True, transport_required='yes').values_list(*values).order_by('team__shift__intime'))

        for emp in employees:
            writer.writerow(emp)

        return response

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
