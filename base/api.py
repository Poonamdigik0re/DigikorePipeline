import datetime
import json
import re
import os

import requests
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from DigikorePortal.settings import CONFIG
from base.models import UserProfile, Project, Shot, Task, Subtask, BidActual, Workstation, Attendance
from utils.celery import logger, error_log

TASK_TYPES = {'rot': 'roto', 'pnt': 'paint', 'cmp': 'comp', 'dpt': 'depth', 'edt': 'editorial', 'prd': 'prod',
              'elmqc': 'elementqc', 'mm': 'matchmove'}


@csrf_exempt
def user_is_artist(request, username):
    try:
        profile = UserProfile.objects.filter(user__username=username).values('designation__is_artist',
                                                                             'designation__name').first()
        is_artist = profile['designation__is_artist']

        if re.search('second lead', profile['designation__name'], re.IGNORECASE):
            is_artist = False
    except:
        is_artist = False

    return HttpResponse(1 if is_artist else 0)


@csrf_exempt
def update_actuals(request, project_name, sequence_name, shot_name, task_name, subtask_name, username, task_type):
    userprofile_full_name = None
    try:
        task_type_name = TASK_TYPES[task_type] if task_type in TASK_TYPES else task_type

        now = datetime.datetime.now()
        user = User.objects.get(username=username)
        userprofile_full_name = user.userprofile.full_name

        project = Project.objects.get(name=project_name)

        assert BidActual.objects.filter(user=user, modified_on__gt=now - datetime.timedelta(
            seconds=296)).count() == 0, "Duplicate request in last 5 minutes."

        # don't do anything for inactive projects
        if project.status.name == "Archived":
            return HttpResponse("This is an archived project.")

        shot = Shot.objects.get(project=project, sequence=sequence_name, name=shot_name)
        task = Task.objects.get(project=project, parent_id=shot.id, parent_type='shot', type__name=task_type_name,
                                name=task_name)
        subtask = Subtask.objects.get(project=project, parent_id=task.id, parent_type='task', name=subtask_name)

        # todo: enable this later
        # assert task.status.name in ['Ready', 'In Progress'], 'This task status is not In Progress.'
        # assert subtask.assignee.username == username, 'This task is not assigned to you.'

        # for morning shift
        attendance = Attendance.objects.filter(user=user, date=now.date(), intime__isnull=False).first()

        if not attendance:
            attendance = Attendance.objects.filter(user=user, date=(now - datetime.timedelta(days=1)).date(),
                                                   intime__isnull=False).first()

        assert attendance, "No Attendance"

        date = attendance.date

        bid_actual, is_new = BidActual.objects.get_or_create(user=user, project=project, shot=shot,
                                                             task=task, subtask=subtask, date=date)

        # for duplicate applications, check if its not getting updated twice
        # keeping a 2 second buffer
        if bid_actual.modified_on > now - datetime.timedelta(seconds=296):
            raise Exception("Duplicate request.")

        # update user bids
        bid_actual.actuals += 300
        bid_actual.modified_on = now
        bid_actual.save()

        # update subtask actuals
        subtask.actuals += 300
        subtask.save()

        # update task actuals
        task.actuals += 300
        task.save()

        # update data in elasticsearch
        data = {
            "project": project_name,
            "sequence": sequence_name,
            "shot": shot_name,
            "task": task_name,
            "subtask": subtask_name,
            "task_type": task_type,
            "user": userprofile_full_name,
            # leave this to utc because kibana works in UTC
            "datetime": datetime.datetime.utcnow().isoformat(),
            "error": ""
        }

        logger.delay('bid_actuals', data)

        return HttpResponse()

    except Exception as error:
        # update data in elasticsearch
        data = {
            "project": project_name,
            "sequence": sequence_name,
            "shot": shot_name,
            "task": task_name,
            "subtask": subtask_name,
            "task_type": task_type,
            "user": userprofile_full_name,
            # leave this to utc because kibana works in UTC
            "datetime": datetime.datetime.utcnow().isoformat(),
            "error": str(error)
        }

        logger.delay('bid_actuals', data)

        return HttpResponseBadRequest(error)


@csrf_exempt
def update_actuals_v2(request):
    data = json.loads(request.body)
    userprofile_full_name = None
    try:
        task_type_name = TASK_TYPES[data['task_type']] if data['task_type'] in TASK_TYPES else data['task_type']

        now = datetime.datetime.now()
        user = User.objects.get(username=data['username'])
        userprofile_full_name = user.userprofile.full_name

        project = Project.objects.get(name=data['project_name'])

        assert BidActual.objects.filter(user=user, modified_on__gt=now - datetime.timedelta(
            seconds=296)).count() == 0, "Duplicate request in last 5 minutes."

        # don't do anything for inactive projects
        if project.status.name == "Archived":
            return HttpResponse("This is an archived project.")

        shot = Shot.objects.get(project=project, sequence=data['sequence_name'], name=data['shot_name'])
        task = Task.objects.get(project=project, parent_id=shot.id, parent_type='shot', type__name=task_type_name,
                                name=data['task_name'])
        subtask = Subtask.objects.get(project=project, parent_id=task.id, parent_type='task', name=data['subtask_name'])

        # todo: enable this later
        # assert task.status.name in ['Ready', 'In Progress'], 'This task status is not In Progress.'
        # assert subtask.assignee.username == username, 'This task is not assigned to you.'

        # for morning shift
        attendance = Attendance.objects.filter(user=user, date=now.date(), intime__isnull=False).first()

        if not attendance:
            attendance = Attendance.objects.filter(user=user, date=(now - datetime.timedelta(days=1)).date(),
                                                   intime__isnull=False).first()

        assert attendance, "No Attendance"

        date = attendance.date

        bid_actual, is_new = BidActual.objects.get_or_create(user=user, project=project, shot=shot,
                                                             task=task, subtask=subtask, date=date)

        # for duplicate applications, check if its not getting updated twice
        # keeping a 2 second buffer
        if bid_actual.modified_on > now - datetime.timedelta(seconds=296):
            raise Exception("Duplicate request.")

        # update user bids
        bid_actual.actuals += 300
        bid_actual.modified_on = now
        bid_actual.save()

        # update subtask actuals
        subtask.actuals += 300
        subtask.save()

        # update task actuals
        task.actuals += 300
        task.save()

        # update data in elasticsearch
        data = {
            "project": data['project_name'],
            "sequence": data['sequence_name'],
            "shot": data['shot_name'],
            "task": data['task_name'],
            "subtask": data['subtask_name'],
            "task_type": data['task_type'],
            "user": userprofile_full_name,
            # leave this to utc because kibana works in UTC
            "datetime": datetime.datetime.utcnow().isoformat(),
            "error": ""
        }

        logger.delay('bid_actuals', data)

        return HttpResponse()

    except Exception as error:
        # update data in elasticsearch
        data = {
            "project": data['project_name'],
            "sequence": data['sequence_name'],
            "shot": data['shot_name'],
            "task": data['task_name'],
            "subtask": data['subtask_name'],
            "task_type": data['task_type'],
            "user": userprofile_full_name,
            # leave this to utc because kibana works in UTC
            "datetime": datetime.datetime.utcnow().isoformat(),
            "error": str(error)
        }

        logger.delay('bid_actuals', data)

        return HttpResponseBadRequest(error)


@csrf_exempt
def save_system_info(request):
    try:
        data = json.loads(request.body)
        workstation, is_new = Workstation.objects.get_or_create(mac=data['mac'])

        for key, value in data.items():
            setattr(workstation, key, value)

        workstation.save()

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(error))
        return HttpResponseBadRequest(error)


@csrf_exempt
def signiant_job_submit(request):
    """
    Create a Signiant Transfer Job and start it.
    :param request: {
        "name": "job name",
        "from": "pnq | lax",
        "to": "lax | pnq",
        "filename" : "*",
        "source": "/path/to/folder",
        "dest": "/path/to/destination"
    }
    :return: {"jobId": 1234, "creator"}
    """
    try:
        data = json.loads(request.body)

        name = data['name']
        from_location = data['from']
        to_location = data['to']
        source_file = data.get('filename', '*')
        source_dir = data['source']
        destination_dir = data.get('dest', source_dir)

        if os.path.isfile(destination_dir):
            destination_dir = os.path.dirname(destination_dir)

        group = "site_sync_jobs"
        library = "sync_jobs"
        template = f"{from_location}_to_{to_location}"

        job_submit_url = 'https://digi-sigmgr.digikore.work/signiant/spring/admin/v1.0/jobs'
        job_start_url = f'https://digi-sigmgr.digikore.work/signiant/spring/admin/v1.0/jobs/command/{name}/{group}/force'

        payload = [{"job":
                        {"jobName": name,
                         "fields": {
                             "jobGroupName": group,
                             "jobTemplateLibraryName": library,
                             "jobTemplateName": template,
                             "jobArgs": {
                                 f"{template}.Schedule.sourceDirectory": source_dir,
                                 f"{template}.Schedule.sourceFile": source_file,
                                 f"{template}.Schedule.targetDirectory": destination_dir}
                         }}
                    }]

        headers = {"username": CONFIG['signiant']['user'], "password": CONFIG['signiant']['password']}

        # Submit a Job Creation Request
        submit_req = requests.post(job_submit_url, data=json.dumps(payload), headers=headers, verify=False)
        submit_resp = submit_req.json()

        if submit_req.ok:
            # Start the Job
            command_req = requests.get(job_start_url, headers=headers, verify=False)
            command_resp = command_req.json()

            if command_req.ok:
                return JsonResponse(submit_resp, safe=False)
            else:
                raise requests.HTTPError(command_resp)
        else:
            raise requests.HTTPError(submit_resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(error))
        return HttpResponseBadRequest(error)
