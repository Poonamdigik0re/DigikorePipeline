import csv
import json
import traceback

from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from DigikorePortal.settings import MODELS
from base.models import BidActual, Attendance, Department
from utils.celery import error_log


def seconds_to_hhmm(seconds):
    if seconds is not None and seconds > 0:
        minutes = seconds / 60
        hours = minutes / 60

        return f'{int(hours)}:{int(minutes % 60)}'
    else:
        return 0


@permission_required('base.artist_utilization')
def home(request):
    return render(request, 'artist_utilization.html')


@permission_required('base.artist_utilization')
def get_departments(request):
    try:
        resp = list(Department.objects.filter(resource_planner=True).values('id', 'name'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.artist_utilization')
def get_data(request):
    try:
        data = json.loads(request.body)
        resp = []

        attendance = Attendance.objects.filter(
            user__userprofile__department_id=data['department_id'],
            user__userprofile__designation__is_artist=True,
            date=data['date']).values(*MODELS['artist_utilization']['attendance']).exclude(
            type__in=['LE', 'LOP']).order_by('user__userprofile__team_id')

        bidactuals = BidActual.objects.filter(date=data['date']).values('user_id', 'actuals')

        for att in attendance:
            att['actuals'] = sum([x['actuals'] for x in bidactuals if x['user_id'] == att['user_id']])
            resp.append(att)

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.artist_utilization')
def download_as_csv(request, date):
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Artist_Utilization_%s.csv"' % date

        writer = csv.writer(response)

        writer.writerow(['Name', 'Department', 'Team Lead', 'Shift', 'In Time', 'Out Time', 'Working Hours',
                         'Production Hours'])

        attendance = Attendance.objects.filter(
            user__userprofile__designation__is_artist=True,
            date=date).values(*MODELS['artist_utilization']['attendance']).exclude(type__in=['LE', 'LOP']).order_by(
            'user__userprofile__team_id')

        bidactuals = BidActual.objects.filter(date=date).values('user_id', 'actuals')

        for att in attendance:
            actuals = sum([x['actuals'] for x in bidactuals if x['user_id'] == att['user_id']])

            writer.writerow([
                att['user__userprofile__full_name'],
                att['user__userprofile__department__name'],
                att['user__userprofile__team__lead__userprofile__full_name'],
                att['user__userprofile__team__shift__name'],
                att['intime'],
                att['outtime'],
                seconds_to_hhmm(att['working_hours']),
                seconds_to_hhmm(actuals),
            ])

        return response

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
