import json
import traceback

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render

from base.models import Attendance, BidActual
from utils.celery import error_log


@login_required
def home(request):
    return render(request, 'my_calendar.html')


@login_required
def get_my_attendance(request):
    try:
        data = json.loads(request.body)
        month = int(data['month'])
        year = int(data['year'])

        resp = list(Attendance.objects.filter(date__year=year, date__month=month, user=request.user).values(
            'date', 'type', 'intime', 'outtime', 'working_hours').order_by('date'))

        for att in resp:
            att['actuals'] = BidActual.objects.filter(user=request.user, date=att['date']).aggregate(Sum('actuals'))[
                'actuals__sum']

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
