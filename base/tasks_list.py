import json
import traceback
import csv
from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render

from DigikorePortal.settings import MODELS
from base.models import *
from utils.celery import error_log
from django.db import connection
from datetime import datetime
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from io import StringIO
from django.core.exceptions import ValidationError

@login_required
def home(request):
    return render(request, 'tasks_list.html')


@permission_required('base.tasks_list')
def get_all_users(request):
    try:
        data = list(User.objects.filter(is_active=True).values('id', 'userprofile__full_name').order_by(
            'userprofile__full_name'))
        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@login_required
def get_user_tasks(request):
    try:
        data = json.loads(request.body)
        print(data)

        user_id = data['user_id']


        shot_values = MODELS['tasks_list']['shot']
        # print("shot_values", shot_values)
        task_values = MODELS['tasks_list']['task']
        # print("task_values", task_values)
        subtask_values = MODELS['tasks_list']['subtask']
        # print("subtask_values", subtask_values)
        data = []

        filters = {'assignee_id': user_id if user_id else request.user.id, 'project__status__name': 'In Progress'}
        # print("filters",filters)

        for task in list(Task.objects.filter(**filters).values(*task_values)):
            # print("#:",task)
            shot = Shot.objects.filter(project_id=task['project_id']).values(*shot_values).first()
            # print("task:",task)
            # print("***")
            # print("shot:",shot)

            if not shot:
                continue

            task['shot__name'] = shot['name']
            task['sequence__name'] = shot['sequence']

            data.append(task)
        # print("*:",data)

        for subtask in list(Subtask.objects.filter(**filters).values(*subtask_values)):
            task = Task.objects.filter(project_id=subtask['project_id'],
                                       id=subtask['parent_id']).values(*task_values).first()
            # print("\nsubtask:",subtask)
            # print("task::",task)

            if not task:
                continue

            shot = Shot.objects.filter(project_id=task['project_id'], id=task['parent_id']).values(*shot_values).first()
            # print("##shot:",shot)

            if not shot:
                continue

            task['shot__name'] = shot['name']
            task['sequence__name'] = shot['sequence']
            task['subtask'] = True
            task['subtask__name'] = subtask['name']
            task['bids'] = subtask['bids']
            task['subtask__actuals'] = subtask['actuals']
            task['assignee__userprofile__full_name'] = subtask['assignee__userprofile__full_name']

            data.append(task)
        # print("\n final data:",data)

        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.tasks_list')
def get_projects(request):
    try:
        data = list(Project.objects.values('id', 'name'))
        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)

@permission_required('base.tasks_list')
def get_task_status(request):
    try:
        resp = {
            'task_statuses': list(
                TaskStatus.objects.values('id', 'name', 'default', 'bg_color', 'fg_color').order_by('-default')),
        }

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(str(error))

@permission_required('base.tasks_list')
def get_task_priority(request):
    try:
        resp = {
            'task_priorities': list(
                TaskPriority.objects.values('id', 'name', 'default', 'bg_color', 'fg_color').order_by('-default')),
        }

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)



@permission_required('base.tasks_list')
def get_assignee(request):
    try:
        data = list(User.objects.filter(is_active=True).values('id', 'userprofile__full_name').order_by(
            'userprofile__full_name'))
        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)

@permission_required('base.tasks_list.add_new_task')
def add_new_task(request):
    if request.method == 'POST':

        data_list = request.POST.getlist('data')
        if data_list:
            data = data_list[0]
            try:
                data = json.loads(data)
                data = {key.strip(): value for key, value in data.items()}  # Remove extra spaces from keys
                task_name = data.get('task_name')
                assign_bid =data.get('assign_bid')
                actuals = data.get('actuals')
                project_id = data.get('project_id')
                description = data.get('description')
                delivered_version = data.get('delivered_version')
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                due_date = data.get('due_date')
                working_first_frame = data.get('working_first_frame')
                working_last_frame = data.get('working_last_frame')
                start_frame = data.get('start_frame')
                end_frame = data.get('end_frame')
                assignee_id = data.get('assignee_id')
                # complexity_id = data.get('select-task_complexity')
                priority_id = data.get('task_priority')
                status_id = data.get('task_status_id')
                type_id = data.get('type_id')
                scope_of_work = data.get('scope_of_work')
                # vendor_id = data.get('vendor_id')
                complexity_id = int(data.get('task_complexity')) if data.get(
                    'complexity_id') else 1  # Assigning 1 as default complexity ID
                # priority_id = int(data.get('priority_id')) if data.get(
                #     'priority_id') else 1  # Assigning 1 as default priority ID
                # status_id = int(data.get('status_id')) if data.get(
                #     'status_id') else 1  # Assigning 1 as default status ID
                type_id = int(data.get('type_id')) if data.get('type_id') else 1  # Assigning 1 as default type ID
                # vendor_id = int(data.get('vendor_id')) if data.get('vendor_id') else 1
                print(data)

                # Validate delivered_version
                if delivered_version == '':
                    delivered_version = None  # Set a default value or None as per your requirement

                # Format date strings
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None
                print("***")

                # Create and save the Task object
                task = Task(
                    name=task_name,
                    bids= assign_bid,
                    actuals=actuals,
                    scope_of_work =scope_of_work,
                    project_id=project_id,
                    description=description,
                    delivered_version=delivered_version,
                    start_date=start_date,
                    end_date=end_date,
                    due_date=due_date,
                    working_first_frame=working_first_frame,
                    working_last_frame=working_last_frame,
                    start_frame=start_frame,
                    end_frame=end_frame,
                    assignee_id=assignee_id,
                    complexity_id=complexity_id,
                    priority_id=priority_id,
                    status_id=status_id,
                    type_id=type_id,
                    # vendor_id=vendor_id
                )
                task.save()
                print("task list********1")

                return HttpResponse('Task added successfully')
            except ValidationError as e:
                error_message = str(e)
                print(f'Validation Error: {error_message}')
                return HttpResponse(f'Error: {error_message}')
            except Exception as e:
                error_message = str(e)
                print(f'Exception Error: {error_message}')
                return HttpResponse(f'Error: {error_message}')
        else:
            return HttpResponse('Error: Data not provided')

    return render(request, 'tasks_list.html')

def display_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        csv_contents = csv_file.read().decode('utf-8').splitlines()
        # Convert the CSV contents to a StringIO objects so it can be parsed by the csv module
        csv_string = StringIO('\n'.join(csv_contents))
        reader = csv.reader(csv_string)
        next(reader)

        with connection.cursor() as cursor:
            cursor.execute("SELECT MAX(id) FROM base_task")
            max_id = cursor.fetchone()[0] or 0

        for row in reader:
            try:
                print(row)
                if len(row) < 21 or not row[1]:
                    continue
                # Increment the id value for each row
                max_id += 1
                task_name = row[1]
                description = row[2]
                bids = float(row[3]) if row[3] != 'Null' else 0.0
                print(description)
                actuals = int(row[4])
                print(actuals)
                start_date = datetime.strptime(row[5], '%Y-%m-%d').date()
                print(start_date)
                end_date = datetime.strptime(row[6], '%Y-%m-%d').date()
                turnover_date = datetime.strptime(row[7], '%Y-%m-%d').date()
                working_first_frame = int(row[8])
                working_last_frame = int(row[9])
                assignee_id = int(row[10])
                complexity_id = int(row[11])
                priority_id = int(row[12])
                project_id = int(row[13])
                status_id = int(row[14])
                type_id = int(row[15])
                vendor_id = int(row[16])
                name = row[17]
                approved_version = int(row[18]) if row[18] != 'Null' else None
                parent_id = int(row[19]) if row[19] != 'Null' else None
                parent_type = row[20] if row[20] != 'Null' else None
                delivered_version = int(row[21])
                working_start_frame = int(row[22]) if row[22] != 'Null' else None
                working_end_frame = int(row[23]) if row[22] != 'Null' else None

                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO base_task (id, task_name, description, bids, actuals, start_date, end_date, turnover_date, working_first_frame, working_last_frame, assignee_id, complexity_id, priority_id, project_id, status_id, type_id, vendor_id, name, approved_version, parent_id, parent_type, delivered_version, working_start_frame, working_end_frame) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        [max_id, task_name, description, bids, actuals, start_date, end_date, turnover_date, working_first_frame,
                         working_last_frame, assignee_id, complexity_id, priority_id, project_id, status_id, type_id, vendor_id,
                         name, approved_version, parent_id, parent_type, delivered_version, working_start_frame, working_end_frame])
                    connection.commit()

            except Exception as e:
                print(f"Error: {e} - Row: {row}")

        return render(request, 'tasks_list.html')
