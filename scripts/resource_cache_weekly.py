import os
import sys

sys.path.append('/opt/repos/DigikorePortal')

os.environ['DJANGO_SETTINGS_MODULE'] = 'DigikorePortal.settings'

import django

django.setup()
###########################################################

from base.models import *
from django.db.models import Sum, Q
import datetime
import re

location_id = Location.objects.get(name='pnq')

resp = [[], []]
weeks = {}
holidays = CompanyHoliday.objects.filter(location_id=location_id, working=False).values_list('date', flat=True)

today = datetime.date.today()
week_start = today - datetime.timedelta(days=today.weekday())

# next 12 months
for i in range(358):
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
    for week, dates in weeks.items():
        start_date = dates[0]

        cache, _ = ResourceCache.objects.get_or_create(date=start_date, department_id=department['id'], weekly=True)
        headcount = UserProfile.objects.filter(
            Q(date_of_leaving__isnull=True) | Q(date_of_leaving__gt=start_date),
            date_of_joining__lte=start_date, department_id=department['id'],
            location_id=location_id,
            designation__is_artist=True).count()

        leave = Attendance.objects.filter(user__userprofile__location_id=location_id,
                                          user__userprofile__department_id=department['id'],
                                          user__userprofile__designation__is_artist=True,
                                          type='LE', date__in=dates).count()

        borrowed = ResourceShare.objects.filter(to_department_id=department['id'],
                                                date__in=dates).aggregate(Sum('count'))['count__sum']
        lend = ResourceShare.objects.filter(from_department_id=department['id'],
                                            date__in=dates).aggregate(Sum('count'))['count__sum']

        # get working hours for that selected week
        working_hours_cache = dict({x['date']: x['working_hours'] for x in list(ResourceCache.objects.filter(
            department_id=department['id'], date__in=dates, weekly=False).values('date', 'working_hours'))})

        working_hours = [working_hours_cache.get(x, 8) for x in dates]
        working_hours_multiplier = sum(working_hours) / (len(working_hours) * 8)

        """
        Working hour multiplier.
        
        If a department has 50 artists and they are working for 12 hours, then the total mandays will be 75.
        If 1 artist is on leave, we will subtract 1.5 mandays instead of 1
        """

        # save cache
        cache.headcount = headcount
        cache.mandays = headcount * len(dates) * working_hours_multiplier  # total mandays in week
        cache.leave = leave * working_hours_multiplier
        cache.borrowed_resources = borrowed * working_hours_multiplier if borrowed else 0
        cache.lend_resources = lend * working_hours_multiplier if lend else 0
        cache.weekdays = len(dates)

        if today in dates:
            till_date = dates[0:dates.index(today)]
            absents = Attendance.objects.filter(user__userprofile__location_id=location_id,
                                                user__userprofile__department_id=department['id'],
                                                user__userprofile__designation__is_artist=True,
                                                type='LOP', date__in=till_date).count()
            # adding 1 otherwise it doesn't count today
            absents += round(headcount * 0.1) * (len(dates[dates.index(today):-1]) + 1)
            cache.absent = absents

        elif today > dates[-1]:
            absents = Attendance.objects.filter(user__userprofile__location_id=location_id,
                                                user__userprofile__department_id=department['id'],
                                                user__userprofile__designation__is_artist=True,
                                                type='LOP', date__in=dates).count()
            cache.absent = absents
        else:
            cache.absent = round(headcount * 0.1) * len(dates)  # 10% of headcount

        # get allocated resources
        match = re.search('(vfx )?(roto|paint|comp)', department['name'], re.IGNORECASE)

        if match:
            dept_id = department['id']
            vfx, dept_name = match.groups()
            project_type = 'Stereo'

            # if vfx project then get the department id of roto, Vfx Roto -> Roto
            if vfx:
                project_type = 'VFX'
                dept_id = Department.objects.get(name=dept_name).id

            allocated = ProjectResource.objects.filter(
                project__type__name=project_type, date__in=dates,
                department_id=dept_id).aggregate(Sum('projected'))['projected__sum']

            cache.allocated = allocated if allocated else 0
        else:
            allocated = ProjectResource.objects.filter(date__in=dates, department_id=department['id']).aggregate(
                Sum('projected'))['projected__sum']

            cache.allocated = allocated if allocated else 0

        cache.save()

        # print(f'''
        # Date : {cache.date}
        # Department : {cache.department.name}
        # Headcount : {cache.headcount}
        # Absent : {cache.absent}
        # Leave : {cache.leave}
        # Working Hours : {cache.working_hours}
        # Mandays : {cache.mandays}
        # Allocated : {cache.allocated}
        # Borrowed : {cache.borrowed_resources}
        # Lend : {cache.lend_resources}
        # Weekdays : {cache.weekdays}
        # ''')
