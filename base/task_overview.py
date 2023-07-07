import json
import traceback

from django.contrib.auth.decorators import permission_required
from django.db.models import Sum
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render

from DigikorePortal.settings import MODELS
from base.models import *
from utils.celery import save_change_log, error_log


@permission_required('base.task_overview')
def home(request, task_id):
    return render(request, 'task_overview.html')


@permission_required('base.task_overview')
def get_data(request, task_id):
    try:
        subtask = list(Subtask.objects.filter(parent_id=task_id).values(*MODELS['task_overview']['subtask']))
        task = dict(Task.objects.filter(id=task_id).values(*MODELS['task_overview']['task']).first())
        shot = dict(Shot.objects.filter(id=task['shot_id']).values(*MODELS['task_overview']['shot']).first())
        project = dict(Project.objects.filter(id=shot['project_id']).values(*MODELS['task_overview']['project']).first())
        print(subtask)
        print(task)
        print(shot)
        print(project)

        task['filerecords'] = list(Filerecord.objects.filter(
            parent_type='task', parent_id=task['id']).order_by('name', '-version').values(
            *MODELS['default']['filerecord']))
        shot['filerecords'] = list(Filerecord.objects.filter(
            parent_type='shot', parent_id=shot['id']).order_by('name', '-version').values(
            *MODELS['default']['filerecord']))
        project['filerecords'] = list(Filerecord.objects.filter(
            parent_type='project', parent_id=project['id']).order_by('name', '-version').values(
            *MODELS['default']['filerecord']))

        task['subtasks'] = subtask
        shot['tasks'] = [task]
        project['shots'] = [shot]

        return JsonResponse(project)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.task_overview')
def get_defaults(request, task_id):
    try:
        resp = {
            'status': list(SubtaskStatus.objects.values('id', 'name', 'default')),
            'assignee': list(
                User.objects.filter(userprofile__designation__is_artist=True).values('id', 'userprofile__full_name'))
        }

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.task_overview_add_subtask')
def add_subtask(request, task_id):
    try:
        data = json.loads(request.body)
        model_id = data.get('model_id', None)

        # check total perc
        total_perc = Subtask.objects.filter(parent_id=data['parent_id']).aggregate(Sum('work_perc'))[
            'work_perc__sum']

        if model_id:
            model = Subtask.objects.get(id=model_id)
            data.pop('model_id')
            data.pop('name')

            total_perc = total_perc - model.work_perc

            if total_perc:
                assert total_perc + int(data['work_perc']) <= 100, "Total working percentage can't be greater than 100%"

            for k, v in data.items():
                if hasattr(model, k) and v:
                    if str(getattr(model, k)) != v:
                        setattr(model, k, v)

                        save_change_log.delay(model.project_id, 'subtask', model_id, k, v, request.user.id)

            model.save()
        else:

            # check for total percentage
            if total_perc:
                assert total_perc + int(data['work_perc']) <= 100, "Total working percentage can't be greater than 100%"

            # for names only lowercase and
            data['name'] = data['name'].strip().lower().replace(' ', '_')

            assert Subtask.objects.filter(parent_id=data['parent_id'],
                                          name=data['name']).count() == 0, "Duplicate entry"

            model = Subtask(**{x: y for x, y in data.items() if y})
            model.save()
            model_id = model.id

        resp = Subtask.objects.filter(id=model_id).values(*MODELS['task_overview']['subtask']).first()

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.task_overview')
def get_bidactuals(request, task_id):
    try:
        data = json.loads(request.body)

        resp = list(BidActual.objects.filter(
            task_id=task_id,
            subtask_id=data['subtask_id'],
        ).values('date', 'user__userprofile__full_name', 'actuals'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
