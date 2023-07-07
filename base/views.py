import datetime
import json
import mimetypes
import re
import traceback

import ldap3
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from DigikorePortal.settings import MODELS, FOLDERS
from base.models import *
from utils.celery import sendmail, error_log

TASK_TYPES = {'rot': 'roto', 'pnt': 'paint', 'cmp': 'comp', 'dpt': 'depth', 'edt': 'editorial', 'prd': 'prod',
              'elmqc': 'elementqc', 'mm': 'matchmove'}



def connect_ldap():
    server = ldap3.Server(CONFIG['ldap']['server'], use_ssl=True)
    connection = ldap3.Connection(server, auto_bind=True, user=CONFIG['ldap']['user'],
                                  password=CONFIG['ldap']['password'], authentication=ldap3.NTLM)

    return connection


@login_required
def get_user_details(request):
    try:
        details = {
            'id': request.user.id,
            'username': request.user.username,
            'full_name': request.user.userprofile.full_name,
            'location_id': request.user.userprofile.location_id,
            'location__name': request.user.userprofile.location.name,
            'password_reset': request.user.userprofile.password_reset,
            'permissions': list(
                [x.replace('base.', '') for x in request.user.get_all_permissions() if x.startswith('base.')])
        }

        return JsonResponse(details)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@login_required
def get_all_locations(request):
    resp = list(Location.objects.values('id', 'name'))

    return JsonResponse(resp, safe=False)


@login_required
def get_all_designations(request):
    resp = list(Designation.objects.values('id', 'name'))

    return JsonResponse(resp, safe=False)


@login_required
def get_all_departments(request):
    resp = list(Department.objects.values('id', 'name'))

    return JsonResponse(resp, safe=False)

# @login_required
# def get_username(request):
#     print("****")
#     resp = list(User.objects.values('id', 'username'))
#     print(resp)
#
#     return JsonResponse(resp, safe=False)


@login_required
def get_all_shifts(request):
    resp = list(Shift.objects.values('id', 'name'))

    return JsonResponse(resp, safe=False)


@login_required
def get_all_skills(request):
    resp = list(Skill.objects.values('id', 'name'))

    return JsonResponse(resp, safe=False)


@login_required
def get_all_confirmation_status(request):
    resp = [x[0] for x in USERPROFILE_CONFIRMATION_CHOICES]

    return JsonResponse(resp, safe=False)


@login_required
def get_all_task_type(request):
    resp = list(TaskType.objects.values('id', 'name'))

    return JsonResponse(resp, safe=False)


@login_required
def get_all_holidays(request):
    resp = list(CompanyHoliday.objects.filter(location_id=request.user.userprofile.location_id,
                                              date__year=datetime.date.today().year).values_list('date', flat=True))

    return JsonResponse(resp, safe=False)


@login_required
def change_password(request):
    try:
        data = json.loads(request.body)
        new_pass = data['new_password']
        conf_pass = data['confirm_password']

        assert new_pass == conf_pass, 'Passwords do not match'

        user_dn = CONFIG['ldap']['user_cn'].format(name=request.user.userprofile.full_name,
                                                   location=request.user.userprofile.location.name)

        ldap_conn = connect_ldap()
        ldap_conn.extend.microsoft.modify_password(user_dn, new_pass)

        # update password reset
        userprofile = request.user.userprofile
        userprofile.password_reset = False
        userprofile.password_reset_on = datetime.date.today()
        userprofile.save()

        logout(request)

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@login_required
def get_model_info(request):
    try:
        data = json.loads(request.body)
        parent_type = data['parent_type']
        parent_id = data['parent_id']
        model_class = globals()[parent_type.title()]

        resp = dict(model_class.objects.filter(id=parent_id).values(*MODELS['default'][parent_type]).first())

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@login_required
def add_note(request):
    try:
        data = json.loads(request.body)
        parent_type = data['parent_type']
        parent_id = data['parent_id']
        text = data['text']
        type_id = data['type_id']

        note = Note(parent_id=parent_id, parent_type=parent_type, text=text, type_id=type_id, created_by=request.user)
        note.save()

        resp = list(Note.objects.filter(id=note.id).values(*MODELS['default']['note']))

        if parent_type == 'bid':
            bid = Bid.objects.get(id=parent_id)

            message = f"""<p style='white-space: pre-line'>
            Hi Team,
            {bid.created_by.userprofile.full_name} has added a new note.
            </p>
            <br>
            <p style='white-space: pre-line; font-weight: bold'>{text}</p>"""

            # Send Email
            email_group = EmailGroup.objects.get(name='BID_UPDATE')
            mail_to = email_group.mail_to.split(';')
            cc_to = email_group.cc_to.split(';') if email_group.cc_to else []

            sendmail.delay(f'BID UPDATE: {bid.client.name} / {bid.project} / {bid.name}', message, mail_to, cc_to)

        # parent = None
        # if parent_type == 'shot':
        #     parent = Shot.objects.filter(id=parent_id).values('msi_record_code', 'project__name')
        # elif parent_type == 'task':
        #     parent = Task.objects.get(id=parent_id).values('msi_record_code', 'project__name', 'type__name')
        #
        # if parent:
        #     update_msi_note.delay(
        #         project_code=parent['project__name'].upper(),
        #         login=request.user.name,
        #         process='SHOT UPDATE' if parent_type == 'shot' else parent['type__name'],
        #         note=text)

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@login_required
def get_notes(request):
    try:
        data = json.loads(request.body)
        parent_type = data['parent_type']
        parent_id = data['parent_id']

        resp = list(Note.objects.filter(parent_type=parent_type, parent_id=parent_id).values(
            *MODELS['default']['note']).order_by('-type__order', '-id'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@login_required
def get_note_types(request):
    try:
        data = list(NoteType.objects.values('id', 'name', 'default'))

        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@login_required
def add_attachments(request):
    try:
        parent_type = request.POST['parent_type']
        parent_id = request.POST['parent_id']
        ids = []

        for x in request.FILES:
            file = File(request.FILES[x])
            file_name = request.FILES[x].name
            file_size = request.FILES[x].size
            file_type, _ = mimetypes.guess_type(file_name)

            attachment = Attachment(parent_id=parent_id, parent_type=parent_type, file=file, created_by=request.user,
                                    name=file_name, size=file_size, type=file_type)
            attachment.save()

            file.close()
            ids.append(attachment.id)

        resp = list(Attachment.objects.filter(id__in=ids).values(
            'id', 'created_on', 'file', 'name', 'size', 'type', 'created_by__userprofile__full_name'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@login_required
def get_attachments(request):
    try:
        data = json.loads(request.body)
        parent_type = data['parent_type']
        parent_id = data['parent_id']

        filters = {'parent_type': parent_type, 'parent_id': parent_id}
        resp = list(Attachment.objects.filter(**filters).values(*MODELS['default']['attachment']).order_by('-id'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@login_required
def get_change_logs(request):
    try:
        data = json.loads(request.body)
        parent_type = data['parent_type']
        parent_id = data['parent_id']

        resp = list(ChangeLog.objects.filter(parent_type=parent_type, parent_id=parent_id).values(
            'id', 'key', 'value', 'created_on', 'created_by__userprofile__full_name'
        ).order_by('-created_on'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@login_required
def browse(request):
    '''
    Use os.scandir to get details of directory

    for f in os.scandir('/mnt'):
        f.is_file()
        f.is_dir()
        f.is_symlink
        f.name => prod
        f.path => /mnt/prod
        f.stat() => os.stat_result(st_mode=16872, st_ino=6991309620, st_dev=45, st_nlink=4, st_uid=0, st_gid=300000, st_size=47, st_atime=1550871112, st_mtime=1550871112, st_ctime=1550871112)

    :param request:
    :return:
    '''
    try:
        data = json.loads(request.body)
        path = data['path'] if data['path'] else FOLDERS['root']['mount']

        # user can not go anywhere outside the root mount
        if not re.match(FOLDERS['root']['mount'], path):
            path = FOLDERS['root']['mount']

        resp = {'path': path, 'files': []}

        for f in os.scandir(path):
            stats = f.stat()
            resp['files'].append({
                'name': f.name,
                'path': f.path,
                'size': stats[6],
                'is_dir': f.is_dir()
            })

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@staff_member_required
def login_as(request):
    uid = request.GET.get('uid', None)

    if uid:
        user = User.objects.get(id=uid)
        logout(request)
        user.backend = 'django_auth_ldap.backend.LDAPBackend'
        login(request, user)

        return HttpResponseRedirect("/")

    all_users = UserProfile.objects.filter(user__is_active=True).values('user_id', 'full_name', 'department__name',
                                                                        'designation__name')

    return render(request, 'login_as.html', {'all_users': all_users})
