import json
import traceback

from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render

from DigikorePortal.settings import MODELS
from base.models import UserProfile, Project, Shot, Task, Subtask, BidActual, Workstation, Attendance
from base.models import *
from utils.celery import error_log

@login_required
def home(request):
    return render(request, 'shot_list.html')

@permission_required('base.shot_list')
def get_all_users(request):
    try:
        data = list(User.objects.filter(is_active=True).values('id', 'userprofile__full_name').order_by(
            'userprofile__full_name'))
        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.shot_list')
def get_shots(request):
    try:

        data = json.loads(request.body)

        # print("*:",data)

        user_id = data['user_id']

        projects = list(Project.objects.filter().values(*MODELS['default']['project']).order_by('-created_on'))


        # project_values = MODELS['project']
        # print(projects)

        shot_values = MODELS['shots_list']['shot']
        shot_values = list(Shot.objects.filter().values(*MODELS['default']['shot']).order_by('-created_on'))
        # for i in shot_values:
        #     print(i)
        #     dept_id = int(i['department'])
        #     print(dept_id)
        #     department_name = list(Department.objects.filter(id=dept_id).values('name'))
        #     i['department']= department_name[0]['name']

        [i.update({'department': list(Department.objects.filter(id=int(i['department'])).values('name'))[0]['name']})
         for i in shot_values]
        # print(shot_values)






        # project = list(Shot.objects.filter().values(*project_values))
        # print(project)

        # shot = list(Shot.objects.filter().values(*shot_values))
        # print(shot)
        # print("shot_values", shot_values)
        # task_values = MODELS['tasks_list']['task']
        # # print("task_values", task_values)
        # subtask_values = MODELS['tasks_list']['subtask']
        # # print("subtask_values", subtask_values)
        # data = []
        #
        # filters = {'assignee_id': user_id if user_id else request.user.id, 'project__status__name': 'In Progress'}
        # # print("filters",filters)
        #
        # for task in list(Task.objects.filter(**filters).values(*task_values)):
        #     print("#:",task)
        #     shot = Shot.objects.filter(project_id=task['project_id']).values(*shot_values).first()
        #     print("task:",task)
        #     print("***")
        #     print("shot:",shot)
        #
        #     if not shot:
        #         continue
        #
        #     task['shot__name'] = shot['name']
        #     task['sequence__name'] = shot['sequence']
        #
        #     data.append(task)
        # # print("*:",data)
        #
        # for subtask in list(Subtask.objects.filter(**filters).values(*subtask_values)):
        #     task = Task.objects.filter(project_id=subtask['project_id'],
        #                                id=subtask['parent_id']).values(*task_values).first()
        #     # print("\nsubtask:",subtask)
        #     # print("task::",task)
        #
        #     if not task:
        #         continue
        #
        #     shot = Shot.objects.filter(project_id=task['project_id'], id=task['parent_id']).values(*shot_values).first()
        #     # print("##shot:",shot)
        #
        #     if not shot:
        #         continue
        #
        #     task['shot__name'] = shot['name']
        #     task['sequence__name'] = shot['sequence']
        #     task['subtask'] = True
        #     task['subtask__name'] = subtask['name']
        #     task['bids'] = subtask['bids']
        #     task['subtask__actuals'] = subtask['actuals']
        #     task['assignee__userprofile__full_name'] = subtask['assignee__userprofile__full_name']
        #
        #     data.append(task)
        # # print("\n final data:",data)

        return JsonResponse(shot_values, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


