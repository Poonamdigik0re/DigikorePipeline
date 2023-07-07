import traceback

from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render

from DigikorePortal.settings import MODELS
from base.models import Workstation
from utils.celery import error_log


@permission_required('base.workstations')
def home(request):
    return render(request, 'workstations.html')


@permission_required('base.workstations')
def get_all_workstations(request):
    try:
        resp = list(Workstation.objects.values(*MODELS['default']['workstation']))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
