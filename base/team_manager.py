import csv
import datetime
import json
import traceback

from django.contrib.auth.decorators import permission_required
from django.http.response import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render

from base.models import Team, UserProfile
from utils.celery import error_log


@permission_required('base.team_manager')
def home(request):
    return render(request, 'team_manager.html')


@permission_required('base.team_manager')
def get_all_teams(request):
    try:
        values = ('id', 'department_id', 'department__name', 'lead_id', 'lead__userprofile__full_name', 'location_id')
        filters = {}

        if request.user.has_perm('base.team_manager_admin'):
            filters['location_id'] = request.user.userprofile.location_id

        elif request.user.has_perm('base.team_manager_manager'):
            filters['department_id'] = request.user.userprofile.department_id

        teams = list(Team.objects.filter(**filters).values(*values))

        return JsonResponse(teams, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.team_manager')
def get_all_employees(request):
    try:
        values = ('user_id', 'full_name', 'team_id')
        filters = {'user__is_active': True}

        if request.user.has_perm('base.team_manager_admin'):
            filters['location_id'] = request.user.userprofile.location_id

        elif request.user.has_perm('base.team_manager_manager'):
            filters['department_id'] = request.user.userprofile.department_id

        resp = list(UserProfile.objects.filter(**filters).values(*values))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.team_manager')
def add_new_team(request):
    try:
        data = json.loads(request.body)
        location_id = data.get('location_id', request.user.userprofile.location_id)
        department_id = data['department_id']
        shift_id = data['shift_id']
        lead_id = data['lead_id']
        # print("***")
        # print(data,location_id,lead_id,department_id)

        # for department manager
        # if request.user.has_perm('base.team_manager_manager') and not request.user.is_superuser:
        #     print("##")
        #     assert request.user.userprofile.department_id == department_id, 'Permission denied'\

        # print(Team)
        #
        # print(Team.objects.filter().values())
        # print("****")
        # test = Team.objects.create(location_id=location_id, department_id=department_id, shift_id=3, lead_id=lead_id)
        # test.some_property = "some value"
        #
        # print("Location: ", test.location)
        # print("Department: ", test.department)
        # print("Shift: ", test.shift)
        # print("Lead: ", test.lead)
        # print("Some Property: ", test.some_property)

        # print("****")
        # print(Team(location_id=location_id, department_id=department_id, shift_id=1, lead_id=lead_id))
        # print(UserProfile.objects.filter())
        # Team.objects.filter(location_id=user_id).update(team_id=None if not team_id else team_id)

        Team(location_id=location_id, department_id=department_id, shift_id=shift_id, lead_id=lead_id).save()

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.team_manager')
def add_team_member(request):
    try:
        data = json.loads(request.body)
        team_id = int(data['team_id'])
        user_id = int(data['user_id'])
        print(user_id)

        # for department manager
        if request.user.has_perm('base.team_manager_manager') and not request.user.is_superuser:
            assert request.user.userprofile.department_id == Team.objects.get(
                id=team_id).department_id, 'Permission denied'

        UserProfile.objects.filter(user_id=user_id).update(team_id=None if not team_id else team_id)

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.team_manager')
def download_as_csv(request):
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="TeamBuilder_%s.csv"' % datetime.date.today().strftime(
            "%Y%m%d")

        writer = csv.writer(response)
        writer.writerow(['Department', 'Name', 'Lead'])

        values = ['department__name', 'full_name', 'team__lead__userprofile__full_name']
        filters = {'user__is_active': True, 'team__isnull': False}

        if request.user.has_perm('base.team_manager_admin'):
            filters['location_id'] = request.user.userprofile.location_id

        elif request.user.has_perm('base.team_manager_manager'):
            filters['department_id'] = request.user.userprofile.department_id

        for user in list(UserProfile.objects.filter(**filters).values_list(*values)):
            writer.writerow(user)

        return response

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
