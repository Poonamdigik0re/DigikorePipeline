import os
import sys

sys.path.append('/opt/repos/DigikorePortal')

os.environ['DJANGO_SETTINGS_MODULE'] = 'DigikorePortal.settings'

import django

django.setup()
###########################################################

from base.models import *

from django.db.models import Q
import datetime

date = datetime.date.today()
location = Location.objects.get(name='pnq')

for department in Department.objects.filter(resource_planner=True):
    cache, _ = ResourceCache.objects.get_or_create(department=department, date=date, weekly=False)

    cache.headcount = UserProfile.objects.filter(Q(date_of_leaving__isnull=True) | Q(date_of_leaving__gt=date),
                                                 date_of_joining__lte=date, department=department,
                                                 location=location, designation__is_artist=True).count()

    # this will be a problem because user get back dated leaves approved
    cache.leave = Attendance.objects.filter(user__userprofile__location=location,
                                            user__userprofile__department=department,
                                            user__userprofile__designation__is_artist=True,
                                            type='LE', date=date).count()

    cache.absent = Attendance.objects.filter(user__userprofile__location=location,
                                             user__userprofile__department=department,
                                             user__userprofile__designation__is_artist=True,
                                             type='LOP', date=date).count()
    cache.save()
