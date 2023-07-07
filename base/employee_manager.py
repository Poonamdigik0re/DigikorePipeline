import csv
import datetime
import json
import traceback
import uuid

import ldap3
from PIL import Image
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from DigikorePortal import settings
from DigikorePortal.settings import CONFIG, MODELS
from base.models import UserProfile, Location
from utils.celery import error_log


def connect_ldap():
    print("connect to ldap")
    server = ldap3.Server(CONFIG['ldap']['server'])
    print(server)

    connection = ldap3.Connection(server, auto_bind=True, user=CONFIG['ldap']['user'],
                                  password=CONFIG['ldap']['password'])
    print(connection)

    return connection


def check_ldap_account(first_name, last_name):
    ldap_conn = connect_ldap()
    count = 0
    full_name = f"{first_name} {last_name}"
    username = f"{first_name}{last_name[0]}".lower()

    ldap_conn.open()

    while True:
        search_filter = f"(cn={full_name})"
        ldap_conn.search('OU=D-Users,DC=digitest,DC=gw', search_filter)

        if ldap_conn.search('OU=D-Users,DC=digitest,DC=gw', f"(cn={full_name})"):
            count += 1

        elif ldap_conn.search('OU=D-Users,DC=digitest,DC=gw', f"(sAMAccountName={username})"):
            count += 1

        elif ldap_conn.search('OU=D-Users,OU=Disable Accounts,DC=digitest,DC=gw', f"(cn={full_name})"):
            count += 1

        elif ldap_conn.search('OU=D-Users,OU=Disable Accounts,DC=digitest,DC=gw', f"(sAMAccountName={username})"):
            count += 1

        else:

            break

        if count > 0:
            full_name = f"{first_name} {last_name}{count}"
            username = f"{last_name}{first_name[0]}{count}".lower()

    return username, full_name


def create_ldap_account(request, user):
    try:
        ldap_conn = connect_ldap()

        # CREATE THE USER
        location_name = user.userprofile.location.name

        uid = user.userprofile.uid
        username = user.username
        email = user.email
        full_name = user.userprofile.full_name
        department = user.userprofile.department.name
        title = user.userprofile.designation.name

        attrs = {
            "givenName": user.first_name,
            "cn": full_name,
            "userPrincipalName": email,
            "sAMAccountName": username,
            "displayName": full_name,
            "name": full_name,
            "mail": email,
            "description": department,
            "department": department,
            "title": title,
            "uidNumber": uid,
            "gidNumber": CONFIG['ldap']['group_gid'],  # default for digi-users
            "loginShell": "/bin/bash",
            "unixHomeDirectory": f"/home/{username}",
        }

        # because some users don't have last name
        if user.last_name:
            attrs['sn'] = user.last_name

        user_dn = CONFIG['ldap']['user_cn'].format(name=user.userprofile.full_name)

        # create user
        ldap_conn.add(user_dn, 'user', attrs)

        # set default password
        ldap_conn.extend.microsoft.modify_password(user_dn, CONFIG['ldap']['default_password'])

        # enable account
        ldap_conn.modify(user_dn, {'userAccountControl': [ldap3.MODIFY_REPLACE, ['512']]})

        for group in ['users', user.userprofile.designation.ldap_group.name]:
            print(group)
            print(CONFIG['ldap']['group_cn'])
            group_dn = CONFIG['ldap']['group_cn'].format(name=f'{group}')
            ldap_conn.extend.microsoft.add_members_to_groups(user_dn, group_dn)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)

    return True


def disable_ldap_account(request, profile):
    ldap_conn = connect_ldap()
    try:
        location_name = profile.location.name
        user_dn = CONFIG['ldap']['user_cn'].format(name=profile.full_name, location=location_name)

        # disable user
        ldap_conn.modify(user_dn, {'userAccountControl': [ldap3.MODIFY_REPLACE, ['2']]})

        # move the user to disabled OU
        disabled_dn = CONFIG['ldap']['disabled_user_ou'].format(location=location_name)
        ldap_conn.modify_dn(user_dn, f'CN={profile.full_name}', new_superior=disabled_dn)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)

    return True


def fix_ldap_group(request, profile):
    ldap_conn = connect_ldap()
    try:
        user_dn = CONFIG['ldap']['user_cn'].format(name=profile.full_name)

        """
        # clear existing groups
        ldap_conn.search(user_dn, '(&(objectclass=person))', attributes=['memberOf'])
        ldap_conn.extend.microsoft.remove_members_from_groups(user_dn, list(ldap_conn.entries[0].memberof))
        """

        new_groups = []
        for group_name in ['digi-users', profile.designation.ldap_group.name]:
            new_groups.append(CONFIG['ldap']['group_cn'].format(name=group_name))

        ldap_conn.extend.microsoft.add_members_to_groups(user_dn, new_groups)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.employee_manager')
def home(request):
    return render(request, 'employee_manager.html')


@permission_required('base.employee_manager')
def get_all_employees(request):
    try:
        values = ('id', 'location_id', 'empid', 'full_name', 'user_id', 'user__username', 'gender',
                  'user__first_name', 'user__last_name',
                  'designation_id', 'designation__name', 'department_id', 'department__name',
                  'confirmation_status', 'date_of_joining')
        filters = {}

        if request.user.has_perm('base.employee_manager_manager') and not request.user.is_staff:
            filters['department_id'] = request.user.userprofile.department_id

        data = list(UserProfile.objects.filter(**filters).values(*values).order_by('id'))

        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.employee_manager_admin')
def add_new_employee(request):
    user = None
    profile = None
    user_id = None

    try:
        data = json.loads(request.POST['data'])
        print("*:", data)
        location_id = request.POST.get('location_id', request.user.userprofile.location_id)
        user_id = data.get('user_id', None)

        old_username = data["username"]
        old_empid = data["emp_id"]
        print(old_username)
        print(old_empid)

        if not user_id:
            first_name = data['first_name'].strip().title()
            last_name = data['last_name'].strip().title()

            full_name = f"{first_name} {last_name}"

            # username, full_name = check_ldap_account(first_name, last_name)
            # print(username)

            # username, full_name = check_ldap_account(first_name, last_name)
            email = f"{old_username}@digitest.gw"

            print(first_name, last_name, old_username, email)

            user = User(first_name=first_name, last_name=last_name, username=old_username, email=email)
            print(user)
            user.save()
            print("*")

            # set default password
            default_password = CONFIG['ldap']['default_password']
            user.set_password(default_password)
            user.save()

            location_name = Location.objects.get(id=location_id).name
            print("***")
            empid = "digi-{0}-{1:04d}".format(location_name.upper(),
                                              UserProfile.objects.filter(location_id=location_id).count() + 1)
            print("****")
            print(user)
            print(full_name, old_empid)

            profile = UserProfile(user=user, full_name=full_name, empid=old_empid, password_reset=True)

            # print("profile data:",profile)

            for k, v in data.items():
                if hasattr(profile, k) and v:
                    setattr(profile, k, v)
            profile.save()

            # create ldap account
            # create_ldap_account(request, user)

        else:
            user = User.objects.get(id=user_id)
            profile = user.userprofile

            data.pop('user_id')
            data.pop('first_name')
            data.pop('last_name')

            for k, v in data.items():
                if hasattr(profile, k) and v:
                    setattr(profile, k, v)

            profile.save()

        # disable user and update AD
        if profile.confirmation_status not in ['confirmed', 'pending']:
            profile.user.is_active = False
            profile.user.groups.clear()
            profile.user.save()

            # remove user's team
            profile.team = None
            profile.save()

            # disable user account
            # disable_ldap_account(request, profile)

        if request.FILES:
            thumbnail_path = f'profile_pictures/{uuid.uuid4()}.jpg'
            with open(f'{settings.MEDIA_ROOT}/{thumbnail_path}', 'wb+') as thumbnail:
                for chunk in request.FILES['profile_picture'].chunks():
                    thumbnail.write(chunk)

            profile.profile_picture = f'/media/{thumbnail_path}'
            profile.save()

            # update thumbnail size
            try:
                image = Image.open(profile.profile_picture)
                image.thumbnail((300, 300))
                image.save(profile.profile_picture)
            except:
                pass

        # update skills
        # if 'skills_id' in data:
        #     profile.skills.set([int(x) for x in data['skills_id']])

        # setup group
        user.groups.clear()
        group = profile.designation.site_group
        group.user_set.add(user)

        return HttpResponse()

    except Exception as error:
        if not user_id:
            if profile:
                profile.delete()
            if user:
                user.delete()

        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.employee_manager_admin')
def get_employee_profile(request):
    try:
        data = json.loads(request.body)

        profile = UserProfile.objects.filter(id=data['id']).values(*MODELS['default']['userprofile']).first()

        return JsonResponse(profile)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.employee_manager_admin')
def download_as_csv(request):
    try:
        response = HttpResponse(content_type='text/csv')
        response[
            'Content-Disposition'] = 'attachment; filename="EmployeeManager_%s.csv"' % datetime.date.today().strftime(
            "%Y%m%d")

        writer = csv.writer(response)
        writer.writerow(['EMPID', 'Full Name', 'Date of Birth', 'Gender', 'Designation', 'Department',
                         'Date of Joining', 'Address', 'Phone', 'Emergency Contact'])

        values = ('empid', 'full_name', 'date_of_birth', 'gender', 'designation__name', 'department__name',
                  'date_of_joining', 'current_address', 'phone', 'emergency_contact')

        for user in list(UserProfile.objects.filter(user__is_active=True).values_list(*values)):
            writer.writerow(user)

        return response

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
