import json
import traceback

import psycopg2
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from base.models import UserProfile, Project
from utils.celery import error_log


@permission_required('base.projects_permission')
def home(request, project_id):
    project_name = Project.objects.get(id=project_id).name

    return render(request, 'projects_permission.html', {'project_name': project_name})


@permission_required('base.projects_permission')
def get_users(request, project_id):
    try:
        project_users = list(Project.objects.get(id=project_id).users.values_list('id', flat=True))

        data = list(UserProfile.objects.filter(user__is_active=True).values(
            'user_id', 'full_name', 'department_id', 'department__name', 'designation_id', 'designation__name'))

        for d in data:
            if d['user_id'] in project_users:
                d['checked'] = True

        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.projects_permission')
def save_permissions(request, project_id):
    try:
        data = json.loads(request.body)
        project = Project.objects.get(id=project_id)

        # Default permissions to users in certail groups
        data['users'].extend(list(User.objects.filter(is_active=True, userprofile__department__name__in=(
            'IT', 'Technology', 'Development', 'Pipeline', 'IO', 'Editorial')).values_list('id', flat=True)))

        project.users.set([int(x) for x in data['users']])
        project.save()

        users = list(project.users.values_list('username', flat=True))
        users.extend(['review', 'dreview', 'dm-service'])

        # update MSI permission
        for host in ['pnq-db01.digikore.work', 'lax-db01.digikore.work']:
            try:
                conn = psycopg2.connect(host=host, dbname="sthpw", user="postgres", password="")
                cursor = conn.cursor()

                msi_users = []
                add_users = []
                delete_users = []

                cursor.execute(f"select username from permission where tool_name='Project' and tag='{project.name}'")

                for line in cursor.fetchall():
                    msi_users.append(line[0])

                for user in users:
                    if user not in msi_users:
                        add_users.append(user)

                for user in msi_users:
                    if user not in users:
                        delete_users.append("'%s'" % user)

                if delete_users:
                    delete_query = """delete from permission 
                    where tool_name='Project' 
                    and tag='{}'
                    and username in ({})""".format(project.name, ", ".join(delete_users))

                    cursor.execute(delete_query)
                    conn.commit()

                if add_users:
                    add_query = """insert into permission (tag, tool_name, username) 
                    values {}""".format(', '.join(["('%s', 'Project', '%s')" % (project.name, x) for x in add_users]))

                    cursor.execute(add_query)
                    conn.commit()

                conn.close()
            except:
                error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))

        # todo: there is an issue with Isilon that is only keeps 16 groups, so temporarily disabling this
        # update_ldap_group.delay(joined_group, f'prj-{project.name.lower()}')
        # update_ldap_group.delay(left_group, f'prj-{project.name.lower()}', remove=True)

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
