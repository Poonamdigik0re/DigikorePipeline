import traceback

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render

from DigikorePortal.settings import MODELS
# from base.models import Asset
from utils.celery import error_log


@login_required
def home(request):
    return render(request, 'asset_library.html')


@login_required
def get_all_assets(request):
    try:
        # assets = list(Asset.objects.values(*MODELS['default']['asset']))

        return JsonResponse({}, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
