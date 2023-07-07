import datetime
import json
import re
import subprocess
import traceback
import uuid

import psycopg2
from PIL import Image
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from DigikorePortal import settings
from DigikorePortal.settings import MODELS
from base.models import Project, ProjectStatus, ProjectType, Client, Vendor, Department, TaskType, EmailGroup, \
    GmailGroup
from utils.celery import save_change_log, create_project_group, create_folder, sendmail, \
    update_msi_project, create_project_signiant_folder, error_log, update_msi_permissions, create_gmail_group, \
    update_gmail_group_members


@permission_required('base.projects_list')
def home(request):
    return render(request, 'projects_list.html')


@permission_required('base.projects_list')
def get_project_defaults(request):
    try:
        resp = {
            'project_types': list(ProjectType.objects.values('id', 'name').order_by('-default')),
            'project_statuses': list(ProjectStatus.objects.values('id', 'name').order_by('-default')),
            'clients': list(Client.objects.values('id', 'name').order_by('name')),
            'vendors': list(Vendor.objects.values('id', 'name').order_by('name')),
            'department': list(Department.objects.values('id', 'name').order_by('name')),
            'default_tasks': list(TaskType.objects.values('id', 'name')),

            'supervisors': list(User.objects.filter(groups__name='supervisor',
                                                    is_active=True).values('id', 'userprofile__full_name')),
            'producers': list(User.objects.filter(groups__name='producer',
                                                  is_active=True).values('id', 'userprofile__full_name')),
            'production': list(User.objects.filter(groups__name='production',
                                                   is_active=True).values('id', 'userprofile__full_name'))
        }

        # print("******:", resp)

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.projects_list')
def get_client_contacts(request):
    try:
        data = json.loads(request.body)

        resp = []
        for contact in Client.objects.filter(id=data['client_id']).values('contacts__id', 'contacts__name'):
            resp.append({'value': contact['contacts__id'], 'text': contact['contacts__name']})

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.projects_list')
def get_all_projects(request):
    try:
        data = json.loads(request.body)
        # print(data)

        filters = {'status__id': data['status__id']}
        # print(filters)
        if data.get('type__id', None):
            filters['type__id'] = data['type__id']

        projects = list(Project.objects.filter(**filters).values(*MODELS['default']['project']).order_by('-created_on'))

        # print("*:", projects)

        producers = list(Project.objects.values('id', 'producers__id'))
        department = list(Project.objects.values('id', 'department__id'))
        supervisors = list(Project.objects.values('id', 'supervisors__id'))
        production = list(Project.objects.values('id', 'production__id'))
        vendors = list(Project.objects.values('id', 'vendors__id'))
        contacts = list(Project.objects.values('id', 'contacts__id'))
        default_tasks = list(Project.objects.values('id', 'default_tasks__id'))
        # print(department)
        # print("$$:",Project.objects.values())

        for project in projects:
            # project_department_id = None
            #
            # for x in department:
            #     # print("x:",x)
            #     # print("id:",x['id'])
            #     # print("project:",project['id'])
            #     # print("department:",x['department__id'])
            #     if x['id'] == project['id'] and x['department__id'] is not None:
            #         project_department_id = x['department__id']
            #         break
            #
            # project['department'] = project_department_id

            project['department'] = [x['department__id'] for x in department if
                                     x['id'] == project['id'] and x['department__id'] is not None]
            project['producers'] = [x['producers__id'] for x in producers if
                                    x['id'] == project['id'] and x['producers__id'] is not None]
            project['supervisors'] = [x['supervisors__id'] for x in supervisors if
                                      x['id'] == project['id'] and x['supervisors__id'] is not None]
            project['production'] = [x['production__id'] for x in production if
                                     x['id'] == project['id'] and x['production__id'] is not None]
            project['vendors'] = [x['vendors__id'] for x in vendors if
                                  x['id'] == project['id'] and x['vendors__id'] is not None]
            project['contacts'] = [x['contacts__id'] for x in contacts if
                                   x['id'] == project['id'] and x['contacts__id'] is not None]
            project['default_tasks'] = [x['default_tasks__id'] for x in default_tasks if
                                        x['id'] == project['id'] and x['default_tasks__id'] is not None]

            # print("***&***:",project['department'])
            # print("***123***:", project['producers'])

        seen = set()
        unique_list = []

        for item in projects:
            # Convert lists in the dictionary to tuples
            cleaned_dict = {k: tuple(v) if isinstance(v, list) else v for k, v in item.items()}

            # Convert each dictionary to a tuple of its items
            item_tuple = frozenset(cleaned_dict.items())

            # Check if the tuple has been seen before
            if item_tuple not in seen:
                # Add the tuple to the set of seen tuples
                seen.add(item_tuple)
                # Add the original dictionary to the unique list
                unique_list.append(item)

        # print("\n\n##123##:",unique_list)

        return JsonResponse(unique_list, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


def setup_gmail_groups(project):
    short_name = re.sub('_\d+', '', project.name).lower()

    internal_groups = [
        {
            'name': f'digikore {short_name.upper()}',
            'email': f'digikore_{short_name}@digikore.com',
            'members': project.producers.all() | User.objects.filter(is_active=True,
                                                                     groups__name__in=['management', 'creative'])
        },
        {
            'name': f'{short_name.upper()} Prod',
            'email': f'{short_name}_prod@digikore.com',
            'members': project.producers.all() | project.production.all()
        },
        {
            'name': f'{short_name.upper()} Supervisors',
            'email': f'{short_name}_sups@digikore.com',
            'members': project.supervisors.all()
        },
        {
            'name': f'{short_name.upper()} Leads',
            'email': f'{short_name}_leads@digikore.com',
            'members': []
        },
        {
            'name': f'{short_name.upper()} All',
            'email': f'{short_name}_all@digikore.com',
            'members': project.producers.all() | project.production.all() | project.supervisors.all() | User.objects.filter(
                is_active=True, groups__name__in=['management', 'creative'])
        },
    ]

    for group in internal_groups:
        gmail_group, is_new = GmailGroup.objects.get_or_create(email=group['email'], name=group['name'])

        if is_new:
            create_gmail_group.delay(gmail_group.id)

        for member in group['members']:
            gmail_group.members.add(member)

        update_gmail_group_members.delay(gmail_group.id)

    return True


@permission_required('base.projects_list_add_project')
def add_new_project(request):
    try:
        data = json.loads(request.POST['data'])

        project_id = data.get('id', "")
        producers = data.get('producers', [])
        department = data.get('department', [])
        supervisors = data.get('supervisors', [])
        production = data.get('production', [])
        contacts = data.get('contacts', [])
        vendors = data.get('vendors', [])
        default_tasks = data.get('default_tasks', [])
        # print("department",department)

        data.pop('producers')
        data.pop('department')
        data.pop('supervisors')
        data.pop('production')
        data.pop('contacts')
        data.pop('vendors')
        data.pop('default_tasks')

        # email_group = EmailGroup.objects.get(name='NEW_PROJECT')
        # mail_to = email_group.mail_to.split(';')
        # cc_to = email_group.cc_to.split(';') if email_group.cc_to else []

        is_new_project = False

        if project_id:
            data.pop('id')
            data.pop('name')
            project = Project.objects.get(id=project_id)

            previous_status = project.status.name

            assert project.status.locked is False, 'This project is locked and can not be updated'

            for k, v in data.items():
                if hasattr(project, k) and v:
                    if str(getattr(project, k)) != v:
                        setattr(project, k, v)
                        # change log
                        print(project,project.id,k,v, request.user.id)
                        save_change_log.delay(project.id, 'project', project.id, k, v, request.user.id)

                        # when someone updates the project status
                        if k == 'status':
                            # send project status update email
                            message = f"""<p style='white-space: pre-line'>
                            Hi Team,

                            {project.created_by.userprofile.full_name} has updated the project status to <b>{project.status.name}</b>.
                            </p>"""

                            # sendmail.delay(
                            #     f'PROJECT UPDATE: {project.client.name} - {project.name} - {project.type.name}',
                            #     message, mail_to, cc_to)

            project.save()

            if previous_status == 'Forecast' and project.status.name == 'In Progress' and not re.match('\w+_\d{3}',
                                                                                                       project.name):
                is_new_project = True

        else:
            data['created_by_id'] = request.user.id
            data['name'] = data['name'].strip().upper()

            project = Project(**{x: y for x, y in data.items() if y})
            project.save()

            is_new_project = True

        if is_new_project:
            # NOTE: CREATE PROJECT IN MSI AND GET THE NAME
            process = subprocess.Popen(
                ['curl', '--request', 'POST', '--header', 'Content-Type: application/json', '--data',
                 '{"username": "omkars"}',
                 f'http://http://127.0.0.1:8000/create_project/{project.type.name}/{project.name}'])

            process.wait()

            process = subprocess.Popen(
                ['curl', '--request', 'POST', '--header', 'Content-Type: application/json', '--data',
                 '{"username": "omkars"}',
                 f'http://http://127.0.0.1:8000/create_project/{project.type.name}/{project.name}'])

            process.wait()

            # pnq_conn = psycopg2.connect(host="localhost", dbname="sthpw", user="postgres", password="Omkar@123")
            # pnq_curr = pnq_conn.cursor()
            # pnq_curr.execute("SELECT code FROM project WHERE code = %s", (project.name,))
            #
            # project.name = pnq_curr.fetchone()[0]
            project.save()

            # pnq_conn.close()

            # create group in AD
            # create_project_group.delay(project.name, project.gid)
            #
            # # create signiant folder
            # create_project_signiant_folder.delay(project.client.name, project.name)
            #
            # # create project folder
            # create_folder.delay('project', project.id)
            #
            # # update project permissions in LA
            # update_msi_permissions.delay(project.name)

        if request.FILES:
            thumbnail_path = f'thumbnails/{uuid.uuid4()}.jpg'
            with open(f'{settings.MEDIA_ROOT}/{thumbnail_path}', 'wb+') as thumbnail:
                for chunk in request.FILES['thumbnail'].chunks():
                    thumbnail.write(chunk)

            project.thumbnail = thumbnail_path
            project.save()

            # update thumbnail size
            try:
                image = Image.open(project.thumbnail)
                image.thumbnail((354, 200))
                image.save(project.thumbnail)
            except:
                pass

        # update ManyToMany
        project.producers.set([int(x) for x in producers])
        project.department.set([int(x) for x in department])
        project.supervisors.set([int(x) for x in supervisors])
        project.production.set([int(x) for x in production])
        project.contacts.set([int(x) for x in contacts])
        project.vendors.set([int(x) for x in vendors])
        project.default_tasks.set([int(x) for x in default_tasks])

        project.save()

        # if project.status.name != 'Forecast':
        #     # update project active state in msi
        #     update_msi_project.delay(project.name, 'active', project.status.name != 'Archived')
        #
        #     # update MSI internal emails
        #     if project.internal_emails != "":
        #         update_msi_project.delay(project.name, 'emails', project.internal_emails)

        # send project creation email
        # if not project_id:
        #     # send project creation email
        #     message = f"""<p style='white-space: pre-line'>
        #     Hi Team,
        #
        #     {project.created_by.userprofile.full_name} has created a new project.</p>
        #     <br>
        #     <table style="border-collapse: collapse; border: 1px solid black; font-family: sans-serif" border="1" cellpadding="5">
        #     <tbody>
        #     <tr>
        #         <th>Client</th>
        #         <td>{project.client.name}</td>
        #     </tr>
        #     <tr>
        #         <th>Project</th>
        #         <td>{project.name}</td>
        #     </tr>
        #     <tr>
        #         <th>type</th>
        #         <td>{project.type.name}</td>
        #     </tr>
        #     </tbody>
        #     </table>
        #     """
        #
        #     # sendmail.delay(f'NEW PROJECT: {project.client.name} - {project.name} - {project.type.name}', message,
        #     #                mail_to, cc_to)
        #
        # # send the archival email
        # if project.status.name == 'Ready for Archival':
        #     message = f"""<p style='white-space: pre-line'>
        #         Hi Team,
        #
        #         {request.user.userprofile.full_name} has marked <b>{project.name}</b> as <b>Ready for Archival</b>.
        #
        #         IT team will start the archival process and delete all the unwanted files.
        #         </p>
        #         """
        #
        #     email_group = EmailGroup.objects.get(name='PROJECT_ARCHIVAL')
        #     mail_to = email_group.mail_to.split(';')
        #     cc_to = email_group.cc_to.split(';') if email_group.cc_to else []
        #
        #     sendmail.delay(f'PROJECT ARCHIVAL: {project.name}', message, mail_to, cc_to)

        project.archive_ready_by = request.user
        project.archive_ready_on = datetime.datetime.now()
        project.save()

        # update gmail groups
        # setup_gmail_groups(project)

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
