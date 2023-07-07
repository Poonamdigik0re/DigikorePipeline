import traceback

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render

from base.models import Project
from utils.celery import error_log

launch = "run rv -flags webviewUrlRight=https://pnq-dev-remote01.digikore.work/rv"


@login_required
def home(request):
    return render(request, 'rv.html')


@login_required
def get_projects(request):
    try:
        resp = list(Project.objects.filter(status__name='In Progress').values('id', 'name'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log().delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
