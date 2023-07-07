import csv
import datetime
import json
import traceback

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from DigikorePortal.settings import MODELS
from base.models import Project, ShotStatus, TaskStatus, TaskType, TaskComplexity, TaskPriority, Shot, Task, \
    ProjectStatus, CompanyHoliday, Vendor, BidActual, Subtask, Department
from utils.celery import save_change_log, wss_publish, error_log


@permission_required('base.projects')
def home(request, project_id):
    return render(request, 'projects.html')


@permission_required('base.projects')
def get_defaults(request, project_id):
    try:
        response = {
            'project_status': list(ProjectStatus.objects.values('id', 'name')),
            'project_type': list(ProjectStatus.objects.values('id', 'name')),
            'shot_status': list(ShotStatus.objects.values(*MODELS['default']['shot_status'])),
            'task_status': list(TaskStatus.objects.values(*MODELS['default']['task_status'])),
            'task_complexity': list(TaskComplexity.objects.values(*MODELS['default']['task_complexity'])),
            'task_priority': list(TaskPriority.objects.values(*MODELS['default']['task_priority'])),
            'task_type': list(TaskType.objects.values(*MODELS['default']['task_type'])),
            'users': list(User.objects.filter(
                userprofile__isnull=False, userprofile__designation__is_artist=False).values('id',
                                                                                             'userprofile__full_name')),
            'vendors': list(Vendor.objects.values('id', 'name')),
            'holidays': list(CompanyHoliday.objects.filter(working=False).values_list('date', flat=True))
        }

        return JsonResponse(response)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


# NOTE: don't add permission here
def project_data(project_id, queries):
    """
    Collect all the data for project, this function is separate because this is in use
    at multiple plates.

    :param project_id:
    :param filter_uuid:
    :return:
    """
    # print("*&*")
    project = Project.objects.filter(id=project_id).values(*MODELS['projects']['project']).first()
    # project = Project.objects.filter(id=project_id).values(*MODELS['projects']['project'])
    # project = list(Project.objects.filter(id=project_id).values(*MODELS['projects']['project']))
    project = list(Project.objects.filter(id=project_id).values(*MODELS['projects']['project']))

    # project = Project.objects.get(id=project_id)
    # project = project.values(*MODELS['projects']['project'])

    # print("!@#:",list(Project.objects.filter(id=project_id).values(*MODELS['projects']['project'])))
    task_query_obj = Q()
    shot_query_obj = Q()

    for k, v in queries.items():
        query_obj = Q()
        for query in v:
            op, key, eq, val = query
            if op == 'OR':
                if k == 'task':
                    task_query_obj |= query_obj
                elif k == 'shot':
                    shot_query_obj |= query_obj
                query_obj = Q()

            if eq == '=':
                query_obj &= Q(**{key: val})
            elif eq == '!=':
                query_obj &= ~Q(**{key: val})
            elif eq == '<':
                query_obj &= Q(**{key + '__lte': val})
            elif eq == '>':
                query_obj &= Q(**{key + '__gte': val})

        if k == 'task':
            task_query_obj |= query_obj
        elif k == 'shot':
            shot_query_obj |= query_obj

    all_tasks = list(Task.objects.filter(task_query_obj, project_id=project_id).order_by('type__order', 'name').values(
        *MODELS['projects']['task']))




    # print(all_tasks)
    all_shots = list(Shot.objects.filter(shot_query_obj, project_id=project_id).values(*MODELS['projects']['shot']))
    # for i in all_shots:
    #     dept_id = int(i['department'])
    #     department_name = list(Department.objects.filter(id=dept_id).values('name'))
    #     i['department']= department_name[0]['name']

    [i.update({'department': list(Department.objects.filter(id=int(i['department'])).values('name'))[0]['name']})for i in all_shots]
    [i.update({'department': list(Department.objects.filter(id=int(i['department'])).values('name'))[0]['name']}) for i
     in all_tasks]



    # print(all_tasks)
        # all_shots.append(i)

        # if dept_id == department_id[0]['id']:
        #     department_name = list(Department.objects.filter(id=dept_id).values('name'))
        #     print(department_name)
        # dept2 = Department.objects.filter(id=dept_id).values(*MODELS['department'])


    def load_project(parent):
        for i in parent:
            # print("###:", i)
            load_shot(i, 'project')


    def load_shot(parent, parent_type):

        parent['shots'] = []
        for x in all_shots:
            # print("*&^%:", x)
            # shot_id =
            # client = Shot.objects.get(id=shot_id)
            # print(x)
            # if x['parent_id'] == parent['id'] and x['parent_type'] == parent_type:
            parent['shots'].append(x)


        # parent['shots'] = [
        #     x for x in all_shots if x['parent_id'] == parent['id'] and x['parent_type'] == parent_type
        # ]
        # print("***:",parent)
        # print("^^^:", parent_type)
            for shot in parent['shots']:

                load_task(shot, 'shot')

    def load_task(parent, parent_type):
        # print('parent:', parent)
        # print('parent_type:', parent_type)
        parent['tasks'] = []



        # print(all_tasks)
        # if x['parent_id'] == parent['id'] and x['parent_type'] == parent_type:
        for x in all_tasks:
            # print('----------------------')
            #
            # print('shot:', parent['id'])
            # print('shot details:', parent)
            #
            # print('task:', x['shot_id'])
            # print('tasks details:', x)
            #
            # print('----------***---------')
            # print('tasks parent', parent)
            # print('----------------------')
            # print('tasks x', x['parent_type'])
            if x['department'] == parent['department'] and x['shot_id'] == parent['id']:
                # print("***:",x)
                # print('--------####---------')
                #
                # print('shot:', parent['id'])
                # print('shot details:', parent)
                #
                # print('task:', x['shot_id'])
                # print('tasks details:', x)
                #
                # print('----------&&&---------')
                parent['tasks'].append(x)

        # print("\n\n",parent)
        # [parent['tasks'].append(x) for x in all_tasks if x['department'] == parent['department']]

    # load project

    load_project(project)

    return project


@permission_required('base.projects')
def get_data(request, project_id):
    """
    Get all the data from project

    :param request:
    :return:
    """
    try:
        data = json.loads(request.body)
        # print("*:",data)
        queries = data['queries']
        # print(queries)
        resp =project_data(project_id, queries)
        # print("$#$:",resp)
        for i in resp:

            return JsonResponse(i, safe=True)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.projects')
def update_model(request, project_id):
    """
    Add or update model

    :param request
    :return: JSON formatted list of items
    """
    try:
        data = json.loads(request.body)
        model_type = data['model_type']
        model_id = data['model_id']

        if model_type == 'shot':
            assert request.user.has_perm('base.projects_add_shot'), 'Permission denied'
        elif model_type == 'task':
            assert request.user.has_perm('base.projects_add_task'), 'Permission denied'
        elif model_type == 'subtask':
            assert request.user.has_perm('base.projects_add_subtask'), 'Permission denied'

        # remove this otherwise becomes a problem
        data.pop('model_type')
        model_class = globals()[model_type.title()]

        model = model_class.objects.get(id=model_id)
        wss_func = "wss_edit_model"

        # remove these keys because we can't update them.
        if hasattr(data, 'model_id'):
            data.pop('model_id')

        if hasattr(data, 'name'):
            data.pop('name')

        if hasattr(data, 'type_id'):
            data.pop('type_id')

        for k, v in data.items():
            if hasattr(model, k) and v:
                if str(getattr(model, k)) != v:
                    setattr(model, k, v)

                    # change log
                    save_change_log.delay(model.project_id, model_type, model.id, k, v, request.user.id)

        model.save()

        # setup response
        resp = dict(model_class.objects.filter(id=model_id).values(*MODELS['default'][model_type]).first())
        resp['model_type'] = model_type

        if model_type == 'shot':
            resp['tasks'] = []

        # update
        wss_publish.delay(f'projects{project_id}', {"func": wss_func, "data": resp})

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.projects_add_task')
def update_selected_tasks(request, project_id):
    try:
        data = json.loads(request.body)
        wss_func = "wss_edit_model"

        for task_id in data['task_ids']:
            model = Task.objects.get(id=task_id)

            for k, v in data.items():
                if hasattr(model, k) and v:
                    if str(getattr(model, k)) != v:
                        setattr(model, k, v)

                        # change log
                        save_change_log.delay(model.project_id, 'task', model.id, k, v, request.user.id)

            model.save()

            # setup response
            resp = dict(Task.objects.filter(id=task_id).values(*MODELS['default']['task']).first())
            resp['model_type'] = 'task'

            # update
            wss_publish.delay(f'projects{project_id}', {"func": wss_func, "data": resp})

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.projects')
def download_as_csv(request, project_id):
    try:
        project = Project.objects.get(id=project_id)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{project.name}.csv"'

        writer = csv.writer(response)

        headers = ['Project', 'Sequence', 'Shot', 'Shot Status', 'Task', 'Task Type', 'Task Status', 'Bids', 'Actuals',
                   'Start Date', 'End Date', 'Assignee']

        writer.writerow(headers)

        shot_values = ('id', 'name', 'status__name')
        task_values = ('name', 'type__name', 'status__name', 'bids', 'actuals', 'start_date', 'end_date',
                       'assignee__userprofile__full_name')

        for proj in Project.objects.filter(id=project_id).values('name'):
            for shot in Shot.objects.filter(project_id=project_id).values(*shot_values):
                for task in Task.objects.filter(project_id=project_id, parent_id=shot['id']).values(*task_values):
                    actuals = task['actuals']
                    if actuals > 0:
                        actuals = round(actuals / 3600 / 8, 2)

                    writer.writerow([proj['name'], shot['sequence'], shot['name'], shot['status__name'],
                                     task['name'], task['type__name'], task['status__name'], task['bids'],
                                     actuals, task['start_date'], task['end_date'],
                                     task['assignee__userprofile__full_name']])

        return response

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.projects')
def get_filter_data(request, project_id):
    try:
        resp = {
            'tasks': {
                'type__name': list(TaskType.objects.values_list('name', flat=True)),
                'status__name': list(TaskStatus.objects.values_list('name', flat=True)),
                'complexity__name': list(TaskComplexity.objects.values_list('name', flat=True)),
                'priority__name': list(TaskPriority.objects.values_list('name', flat=True))
            },
            'shots': {
                'name': list(Shot.objects.filter(project_id=project_id).values_list('name', flat=True).distinct()),
                'status__name': list(ShotStatus.objects.values_list('name', flat=True)),
            },
        }

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.projects')
def get_filter_values(request, project_id):
    try:
        data = json.loads(request.body)
        model = data['model']
        key = data['key']
        values = []

        if model == 'shot':
            values = list(set(Shot.objects.filter(project_id=project_id).values_list(key, flat=True)))
        elif model == 'task':
            values = list(set(Task.objects.filter(project_id=project_id).values_list(key, flat=True)))

        return JsonResponse(values, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.projects')
def download_actuals_breakdown(request, project_id):
    try:
        project = Project.objects.filter(id=project_id).values('id', 'name', 'start_date').first()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s_Actuals_Breakdown.csv"' % project['name']

        writer = csv.writer(response)

        assert project['start_date'] is not None, "Please set the project start date."

        start_date = project['start_date']
        today = datetime.date.today()
        days = (today - start_date).days

        dates = []
        resp = ["Project", "Sequence", "Shot", "Task", "Task Type", "Task Status", "Bids", "Actuals"]

        for i in range(days):
            date = start_date + datetime.timedelta(days=i)
            dates.append(date)
            resp.append(date.strftime('%Y-%m-%d'))

        writer.writerow(resp)

        sequence_values = ('id', 'name')
        shot_values = ('id', 'name', 'sequence')
        task_values = ('id', 'name', 'type__name', 'status__name', 'bids', 'actuals')

        for shot in Shot.objects.filter(project_id=project['id']).values(*shot_values):
            for task in Task.objects.filter(project_id=project['id'], parent_type='shot',
                                            parent_id=shot['id']).values(*task_values):
                row = [project['name'], shot['sequence'], shot['name'], task['name'], task['type__name'],
                       task['status__name'], task['bids'], task['actuals'] / 3600 / 8 if task['actuals'] else 0]

                for date in dates:
                    actuals = BidActual.objects.filter(
                        project_id=project['id'], shot_id=shot['id'], task_id=task['id'], date=date).aggregate(
                        Sum('actuals'))['actuals__sum']

                    row.append(actuals / 3600 / 8 if actuals else '')

                writer.writerow(row)

        return response

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.projects')
def download_artist_actuals_breakdown(request, project_id):
    try:
        project = Project.objects.filter(id=project_id).values('id', 'name', 'start_date').first()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s_Artist_Actuals_Breakdown.csv"' % project['name']

        writer = csv.writer(response)

        writer.writerow(['Project', 'Sequence', 'Shot', 'Shot Status', 'Task', 'Task Type', 'Task Status', 'Subtask',
                         'Assignee', 'Date', 'Actuals'])

        seq_values = ('id', 'name')
        shot_values = ('id', 'name', 'status__name')
        task_values = ('id', 'name', 'type__name', 'status__name')
        bidactual_values = ('date', 'actuals', 'user__userprofile__full_name')

        for shot in Shot.objects.filter(project_id=project['id']).values(*shot_values):
            for task in Task.objects.filter(project_id=project['id'], parent_id=shot['id']).values(*task_values):
                for subtask in Subtask.objects.filter(project_id=project['id'],
                                                      parent_id=task['id']).values('id', 'name'):

                    for actual in BidActual.objects.filter(project_id=project['id'],
                                                           shot_id=shot['id'], task_id=task['id'],
                                                           subtask_id=subtask['id']).values(*bidactual_values):
                        row = [project['name'], shot['sequence'], shot['name'], shot['status__name'],
                               task['name'], task['type__name'], task['status__name'], subtask['name'],
                               actual['user__userprofile__full_name'], actual['date'],
                               round(actual['actuals'] / 3600 / 8, 2) if actual['actuals'] else 0]

                        writer.writerow(row)

        return response

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.projects')
def download_aggregated_actuals_report(request, project_id):
    try:
        project = Project.objects.filter(id=project_id).values('id', 'name', 'start_date').first()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s_Aggregated_Actuals_Report.csv"' % project['name']

        writer = csv.writer(response)

        writer.writerow(['Empid', 'Username', 'Department', 'Designation', 'Date', 'Actuals (Days)'])

        values = ('actuals', 'date', 'user_id',
                  'user__userprofile__full_name',
                  'user__userprofile__empid',
                  'user__userprofile__department__name',
                  'user__userprofile__designation__name')

        users = {}

        for actual in BidActual.objects.filter(project_id=project_id).values(*values):
            if actual['user_id'] not in users.keys():
                users[actual['user_id']] = {
                    'empid': actual['user__userprofile__empid'],
                    'full_name': actual['user__userprofile__full_name'],
                    'department': actual['user__userprofile__department__name'],
                    'designation': actual['user__userprofile__designation__name'],
                    'dates': {}
                }

            if actual['date'] not in users[actual['user_id']]['dates']:
                users[actual['user_id']]['dates'][actual['date']] = 0

            users[actual['user_id']]['dates'][actual['date']] += actual['actuals']

        for uid, user in users.items():
            for date, actual in user['dates'].items():
                writer.writerow([
                    user['empid'],
                    user['full_name'],
                    user['department'],
                    user['designation'],
                    date,
                    round(actual / 3600 / 8, 2)
                ])

        return response

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
