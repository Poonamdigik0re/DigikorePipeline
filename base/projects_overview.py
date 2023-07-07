import traceback

from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render

from base.models import Task, Shot, Project
from utils.celery import error_log

TASK_VALUES = ('name', 'bids', 'status_id')


@permission_required('base.projects_overview')
def home(request, project_id):
    project_name = Project.objects.get(id=project_id).name
    return render(request, 'projects_overview.html', {'project_name': project_name})


@permission_required('base.projects_overview')
def get_project_data(request, project_id):
    try:
        labels = list(Task.objects.filter(project_id=project_id).values_list('type__name', flat=True).distinct())

        total_shots = Shot.objects.filter(project_id=project_id).count()
        all_tasks = Task.objects.filter(project_id=project_id,
                                        parent_type='shot').values('id', 'status__name', 'status__bg_color',
                                                                   'type__name', 'working_first_frame',
                                                                   'working_last_frame')

        resp = {'data': [], 'tables': {}}

        for label in labels:
            data = {
                'data': [total_shots],
                'labels': ['-'],
                'backgroundColor': ['#eee']
            }
            d = {}
            e = {}
            tasks = [x for x in all_tasks if x['type__name'] == label]

            if tasks:
                for task in tasks:
                    total_frames = 0

                    if task['working_first_frame'] and task['working_last_frame']:
                        total_frames = task['working_last_frame'] - task['working_first_frame'] + 1

                    if task['status__name'] not in d:
                        d[task['status__name']] = 1
                        data['backgroundColor'].append(task['status__bg_color'])

                        e[task['status__name']] = {'frames': total_frames, 'count': 1}

                    else:
                        d[task['status__name']] += 1
                        e[task['status__name']]['frames'] += total_frames
                        e[task['status__name']]['count'] += 1

                    data['data'][0] -= 1

                for k, v in d.items():
                    data['data'].append(v)
                    data['labels'].append(f'{k} - {v}')

                resp['data'].append({'name': label, 'data': data})
                resp['tables'][label] = e

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
