import csv
import datetime
import json
import re
import traceback

from django.contrib.auth.decorators import permission_required
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from DigikorePortal.settings import MODELS
from base.models import UserProfile, Location, Attendance, Project, ResourceCache, Department, ProjectResource, Task, \
    ResourceShare, CompanyHoliday
from utils.celery import error_log, logger

# location_id = Location.objects.get(name='pnq').id
location_id = 1


@permission_required('base.resource_planner')
def home(request):
    return render(request, 'resource_planner.html')


@permission_required('base.resource_planner')
def get_departments(request):
    try:
        resp = list(Department.objects.filter(resource_planner=True).values('id', 'name').order_by('order'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.resource_planner')
def get_headcount(request):
    try:
        data = json.loads(request.body)

        department_id = data['department_id']
        date_range = [datetime.datetime.strptime(str(x), '%Y%m%d').date() for x in data['date_range']]
        today = datetime.date.today()

        resp = []
        for dt in date_range:
            if dt < today:
                resp.append(ResourceCache.objects.get(department_id=department_id, date=dt, weekly=False).headcount)
            else:
                resp.append(UserProfile.objects.filter(Q(date_of_leaving__isnull=True) | Q(date_of_leaving__gt=dt),
                                                       date_of_joining__lte=dt, department_id=department_id,
                                                       location_id=location_id,
                                                       designation__is_artist=True).count())

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.resource_planner')
def get_working_hours(request):
    try:
        data = json.loads(request.body)

        department_id = data['department_id']
        date_range = [datetime.datetime.strptime(str(x), '%Y%m%d').date() for x in data['date_range']]

        resp = []
        for dt in date_range:
            try:
                resp.append(ResourceCache.objects.get(department_id=department_id, date=dt, weekly=False).working_hours)
            except:
                resp.append(8)

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.resource_planner')
def get_resource_share(request):
    try:
        data = json.loads(request.body)
        department_id = data['department_id']
        date_range = [datetime.datetime.strptime(str(x), '%Y%m%d').date() for x in data['date_range']]

        borrowed = {}

        for share in ResourceShare.objects.filter(to_department_id=department_id,
                                                  date__in=date_range).values('date', 'count'):
            date = share['date'].strftime('%Y-%m-%d')

            if date not in borrowed:
                borrowed[date] = 0

            borrowed[date] += share['count']

        resp = {
            'borrowed': borrowed,
            'lend': list(ResourceShare.objects.filter(
                from_department_id=department_id, date__in=date_range).values('date', 'to_department_id', 'count'))
        }

        return JsonResponse(resp, safe=True)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.resource_planner')
def get_leaves(request):
    try:
        data = json.loads(request.body)

        department_id = data['department_id']
        date_range = [datetime.datetime.strptime(str(x), '%Y%m%d').date() for x in data['date_range']]
        today = datetime.date.today()

        resp = []
        for dt in date_range:
            if dt < today:
                resp.append(ResourceCache.objects.get(department_id=department_id, date=dt, weekly=False).leave)
            else:
                resp.append(Attendance.objects.filter(user__userprofile__location_id=location_id,
                                                      user__userprofile__department_id=department_id,
                                                      user__userprofile__designation__is_artist=True,
                                                      type='LE', date=dt).count())
        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.resource_planner')
def get_absents(request):
    try:
        data = json.loads(request.body)
        department_id = data['department_id']
        date_range = [datetime.datetime.strptime(str(x), '%Y%m%d').date() for x in data['date_range']]

        today = datetime.date.today()
        resp = []
        for dt in date_range:
            if dt < today:
                resp.append(ResourceCache.objects.get(department_id=department_id, date=dt, weekly=False).absent)
            else:
                resp.append(
                    round(UserProfile.objects.filter(Q(date_of_leaving__isnull=True) | Q(date_of_leaving__gt=dt),
                                                     date_of_joining__lte=dt, department_id=department_id,
                                                     location_id=location_id,
                                                     designation__is_artist=True).count() * 0.1))
        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.resource_planner')
def get_holidays(request):
    try:
        data = json.loads(request.body)
        date_range = [datetime.datetime.strptime(str(x), '%Y%m%d').date() for x in data['date_range']]
        resp = list(CompanyHoliday.objects.filter(location_id=location_id,
                                                  working=False, date__in=date_range).values_list('date', flat=True))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.resource_planner')
def get_projects(request):
    """
    :param request:
    :return: For Roto, Paint and Comp, give either Stereo or VFX projects, for everything else return both. Also, filter
    for projects where default tasks has the selected department.
    """
    try:
        data = json.loads(request.body)
        department_id = data['department_id']
        department_name = data['department_name']
        date_range = [datetime.datetime.strptime(str(x), '%Y%m%d').date() for x in data['date_range']]

        filters = {}
        match = re.search('(vfx )?(roto|paint|comp)', department_name, re.IGNORECASE)

        if match:
            vfx, department_name = match.groups()
            filters['type__name'] = 'VFX' if vfx else 'Stereo'

            if vfx:
                department_id = Department.objects.get(name=department_name).id

        filters['default_tasks__department_id'] = department_id

        projects = list(Project.objects.filter(**filters).values(
            *MODELS['resource_planner']['project']).order_by('status__order', '-id'))

        for proj in projects:
            bids = Task.objects.filter(project_id=proj['id'], type__department_id=department_id).aggregate(Sum('bids'))[
                'bids__sum']
            projected = ProjectResource.objects.filter(
                project_id=proj['id'], department_id=department_id).exclude(date__in=date_range).aggregate(
                Sum('projected'))['projected__sum']

            actuals = Task.objects.filter(
                project_id=proj['id'], type__department_id=department_id).aggregate(Sum('actuals'))['actuals__sum']

            proj['bids'] = bids if bids else 0
            proj['actuals'] = actuals / 3600 / 8 if actuals and actuals > 0 else 0
            proj['projected'] = projected if projected and projected > 0 else 0
            proj['variance'] = proj['bids'] - proj['actuals']

        return JsonResponse(projects, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.resource_planner')
def get_resources(request):
    """

    :param request:
    :return: For Roto, Paint and Comp, give either Stereo or VFX project resources, for everything else return both.
    Also, filter for resources where department is same as requested.
    """
    try:
        data = json.loads(request.body)
        department_id = data['department_id']
        department_name = data['department_name']
        date_range = [datetime.datetime.strptime(str(x), '%Y%m%d').date() for x in data['date_range']]

        filters = {'date__in': date_range, 'department_id': department_id}
        match = re.search('(vfx )?(roto|paint|comp)', department_name, re.IGNORECASE)

        if match:
            vfx, department_name = match.groups()
            filters['project__type__name'] = 'VFX' if vfx else 'Stereo'

            if vfx:
                department_id = Department.objects.get(name=department_name).id
                filters['department_id'] = department_id

        resp = list(ProjectResource.objects.filter(**filters).values('date', 'project_id', 'projected', 'actual'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.resource_planner_update')
def update_working_hours(request):
    try:
        data = json.loads(request.body)

        date = datetime.datetime.strptime(str(data['date']), '%Y%m%d').date()
        department_id = data['department_id']
        working_hours = data['working_hours']

        cache, _ = ResourceCache.objects.get_or_create(department_id=department_id, date=date, weekly=False)
        cache.working_hours = working_hours
        cache.save()

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.resource_planner_update')
def add_resources(request):
    """
    For VFX departments, replace it with the normal department, for example, Vfx Roto = Roto
    :param request:
    :return:
    """
    try:
        data = json.loads(request.body)
        department_id = data['department_id']
        department_name = data['department_name']

        assert department_id != "" and department_name != "", 'Missing data'

        project_id = Project.objects.get(name=data['project']).id
        date = datetime.datetime.strptime(str(data['date']), '%Y%m%d').date()

        kwargs = {'location_id': location_id, 'department_id': department_id, 'project_id': project_id, 'date': date}
        match = re.search('(vfx )(roto|paint|comp)', department_name, re.IGNORECASE)

        if match:
            kwargs['department_id'] = Department.objects.get(name=match.groups()[1]).id

        # todo: enable this later
        # assert date >= datetime.date.today(), "Not allowed to make back dated changes"

        resource, is_new = ProjectResource.objects.get_or_create(**kwargs)

        resource.modified_by = request.user
        resource.projected = data['value'] if data['value'] != "" else 0
        resource.save()

        # Update data in kibana
        data = {
            "department": department_name,
            "project": data["project"],
            "datetime": datetime.datetime.utcnow(),
            "date": resource.date.strftime("%a %b %d, %Y"),
            "user": request.user.userprofile.full_name,
            "value": resource.projected
        }

        logger.delay('resource_planner', data)

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.resource_planner_update')
def add_resource_share(request):
    try:
        data = json.loads(request.body)
        date = datetime.datetime.strptime(str(data['date']), '%Y%m%d').date()
        from_department_id = data['from_department_id']
        to_department_id = data['to_department_id']
        count = data['count']

        resource_share, is_new = ResourceShare.objects.get_or_create(date=date,
                                                                     from_department_id=from_department_id,
                                                                     to_department_id=to_department_id)
        resource_share.count = count
        resource_share.save()

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.resource_planner')
def get_annual_projection(request):
    try:
        resp = [[], []]
        weeks = {}
        holidays = CompanyHoliday.objects.filter(location_id=location_id, working=False).values_list('date', flat=True)

        start_date = datetime.date.today()
        week_start = start_date - datetime.timedelta(days=start_date.weekday())

        # 6 months
        for i in range(182):
            date = week_start + datetime.timedelta(days=i)
            week = date.strftime('%V')

            if week not in weeks:
                weeks[week] = []

            if date.weekday() < 5 and date not in holidays:
                weeks[week].append(date)

        for week, dates in weeks.items():
            resp[0].append(dates[0].strftime('%b %d'))
            resp[1].append(dates[0].strftime('%Y'))

        for department in Department.objects.filter(resource_planner=True).order_by('order').values('id', 'name'):
            data1 = [f'{department["name"]} Resources']
            data2 = [f'{department["name"]} Allocated']
            data3 = [f'{department["name"]} Available']

            for week, dates in weeks.items():
                start_date = dates[0]
                cache = ResourceCache.objects.get(date=start_date, department_id=department['id'], weekly=True)

                mandays = cache.mandays + cache.borrowed_resources - cache.lend_resources - cache.leave - cache.absent

                data1.append(mandays)
                data2.append(cache.allocated)
                data3.append(mandays - cache.allocated)

            resp.append(data1)
            resp.append(data2)
            resp.append(data3)
            resp.append([])

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.resource_planner')
def get_annual_charts(request):
    try:
        weeks = {}
        holidays = CompanyHoliday.objects.filter(location_id=location_id, working=False).values_list('date', flat=True)

        start_date = datetime.date.today()
        week_start = start_date - datetime.timedelta(days=start_date.weekday())

        # 6 months
        for i in range(365):
            date = week_start + datetime.timedelta(days=i)
            week = date.strftime('%V')

            if week not in weeks:
                weeks[week] = []

            if date.weekday() < 5 and date not in holidays:
                weeks[week].append(date)

        datasets = {
            'labels': [],
            'data': {},
        }

        for week, dates in weeks.items():
            datasets['labels'].append(dates[0].strftime('%b %d'))

        for department in Department.objects.filter(resource_planner=True).order_by('order').values('id', 'name'):
            datasets['data'][department['name']] = {
                'mandays': {'label': 'Mandays', 'backgroundColor': [], 'data': []},
                'allocated': {'label': 'Allocated', 'backgroundColor': [], 'data': []},
                'available': {'label': 'available', 'backgroundColor': [], 'data': []},
                'projects': {}
            }
            for week, dates in weeks.items():
                cache = ResourceCache.objects.get(date=dates[0], department_id=department['id'], weekly=True)

                mandays = cache.mandays + cache.borrowed_resources - cache.lend_resources - cache.leave - cache.absent

                datasets['data'][department['name']]['mandays']['data'].append(mandays)
                datasets['data'][department['name']]['mandays']['backgroundColor'].append('#555555')

                datasets['data'][department['name']]['allocated']['data'].append(cache.allocated)
                datasets['data'][department['name']]['allocated']['backgroundColor'].append('#ffc107')

                datasets['data'][department['name']]['available']['data'].append(mandays - cache.allocated)
                datasets['data'][department['name']]['available']['backgroundColor'].append('#2ecc71')

                filters = {'default_tasks__department_id': department['id']}
                match = re.search('(vfx )?(roto|paint|comp)', department['name'], re.IGNORECASE)

                if match:
                    vfx, department_name = match.groups()
                    filters['type__name'] = 'VFX' if vfx else 'Stereo'

                    if vfx:
                        filters['default_tasks__department_id'] = Department.objects.get(name=department_name).id

                for project in Project.objects.filter(**filters).values('id', 'name'):
                    if project['name'] not in datasets['data'][department['name']]['projects']:
                        datasets['data'][department['name']]['projects'][project['name']] = {
                            'label': project['name'],
                            'data': []
                        }

                    resources = ProjectResource.objects.filter(date__in=dates,
                                                               department_id=filters['default_tasks__department_id'],
                                                               project_id=project['id']).aggregate(Sum('projected'))

                    projected = resources['projected__sum'] if resources['projected__sum'] else 0
                    datasets['data'][department['name']]['projects'][project['name']]['data'].append(projected)

        return JsonResponse(datasets, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.resource_planner')
def download_as_csv(request):
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="resource_planner.csv"'

        holidays = CompanyHoliday.objects.filter(location_id=location_id, working=False).values_list('date', flat=True)

        resp = [[''], ['Week']]
        weeks = {}
        start_date = datetime.date.today()
        week_start = start_date - datetime.timedelta(days=start_date.weekday())

        # 6 months
        for i in range(182):
            date = week_start + datetime.timedelta(days=i)
            week = date.strftime('%V')

            if week not in weeks:
                weeks[week] = []
                resp.append([date.strftime('%b %d, %Y')])

            if date.weekday() < 5 and date not in holidays:
                weeks[week].append(date)

        for department in Department.objects.filter(resource_planner=True).order_by('order').values('id', 'name'):
            resp[0].append(department['name'])
            resp[0].append(department['name'])
            resp[1].append('Mandays')
            resp[1].append('Available')

            counter = 2
            for week, dates in weeks.items():
                cache = ResourceCache.objects.get(date=dates[0], department_id=department['id'], weekly=True)
                mandays = cache.mandays + cache.borrowed_resources - cache.lend_resources - cache.leave - cache.absent

                resp[counter].append(mandays)
                resp[counter].append(round(mandays - cache.allocated, 2))

                counter += 1

        writer = csv.writer(response)

        for line in resp:
            writer.writerow(line)

        return response

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
