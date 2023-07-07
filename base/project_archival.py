import datetime
import json
import traceback

from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from base.models import Project, ProjectStatus, EmailGroup
from utils.celery import sendmail, archive_project, error_log


@permission_required('base.project_archival')
def home(request):
    return render(request, 'project_archival.html')


@permission_required('base.project_archival')
def get_projects(request):
    try:
        values = ('id', 'name', 'archive_ready_on', 'archive_started_on', 'archive_started_by__userprofile__full_name',
                  'archive_completed_on', 'status__name', 'archive_size')
        resp = list(
            Project.objects.filter(status__name__icontains='archiv').order_by('-created_on').values(
                *values))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.project_archival')
def start_archival(request):
    try:
        data = json.loads(request.body)
        project = Project.objects.get(id=data['project_id'])

        assert project.status.locked is False, "This project is locked and cannot be modified"

        project.status = ProjectStatus.objects.get(name='Archival In Progress')
        project.archive_started_by = request.user
        project.archive_started_on = datetime.datetime.now()
        project.save()

        email_group = EmailGroup.objects.get(name='PROJECT_ARCHIVAL')
        mail_to = email_group.mail_to.split(';')
        cc_to = email_group.cc_to.split(';') if email_group.cc_to else []
        message = f"""<p style='white-space: pre-line'>
        Hi Team,

        {request.user.userprofile.full_name} has started the archival for <b>{project.name}</b>.
        </p>
        """

        sendmail.delay(f'PROJECT ARCHIVAL: {project.name}', message, mail_to, cc_to)

        # start the archival process
        archive_project.delay(project.name)

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
