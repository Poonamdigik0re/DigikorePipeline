import os
import sys

sys.path.append('/opt/repos/DigikorePortal')

os.environ['DJANGO_SETTINGS_MODULE'] = 'DigikorePortal.settings'

import django

django.setup()
###########################################################

from base.models import *

import pymssql
import time
import datetime
import traceback

IN_READERS = [539336977, 539345374, 539336976]
OUT_READERS = [539336987, 539345394]

conn = pymssql.connect('10.30.10.71', 'biostar', 'All0Wm$', 'BioStar')
cursor = conn.cursor(as_dict=True)

# device is adding IST time in utc, adding 19800 to fix that bug
# 86400 seconds = 1 day
# 3600 seconds = 1 hour
now = int(time.time()) + 19800 - 1800

cursor.execute("""SELECT nDateTime, nReaderIdn, nEventIdn, nUserID
                  FROM BioStar.dbo.TB_EVENT_LOG
                  WHERE nDateTime>%d AND (nEventIdn=55 OR nEventIdn=47)""", now)

rows = cursor.fetchall()
today = datetime.date.today()

# cache all shifts
shifts = list(Shift.objects.all().values('id', 'name', 'intime'))

for shift in shifts:
    shift['members'] = []
    for team in Team.objects.filter(shift=shift['id']):
        members = list(UserProfile.objects.filter(team=team).values_list('user_id', flat=True))
        shift['members'].extend(members)

for row in rows:
    try:
        empid = 'digi-%s-%04d' % ('pnq', row['nUserID'])
        reader_id = row['nReaderIdn']
        timestamp = datetime.datetime.fromtimestamp(row['nDateTime'] - 19800)

        user = User.objects.get(userprofile__empid=empid)
        intime = None

        for shift in shifts:
            if user.id in shift['members']:
                intime = shift['intime']

        # Artists who worked more than 11 hours yesterday can come 30 minutes late and who worked
        # more than 12 hours can come 1 hour late to office
        for last_att in Attendance.objects.filter(user=user, date=timestamp.date() - datetime.timedelta(days=1),
                                                  working_hours__gte=39600):
            if last_att.working_hours >= 39600:
                intime = (datetime.datetime.combine(datetime.date(2019, 1, 1), intime) + datetime.timedelta(
                    minutes=30)).time()

            if last_att.working_hours >= 43200:
                intime = (datetime.datetime.combine(datetime.date(2019, 1, 1), intime) + datetime.timedelta(
                    minutes=60)).time()

        if reader_id in IN_READERS:
            att, is_new = Attendance.objects.get_or_create(user=user, date=timestamp.date())

            if is_new or att.type == 'LOP':
                att.type = 'LT' if intime and timestamp.time() > intime else 'IN'
                att.intime = timestamp
                att.save()

        elif reader_id in OUT_READERS:
            atts = Attendance.objects.filter(user=user, date=timestamp.date(), intime__isnull=False)

            if not atts:
                atts = Attendance.objects.filter(user=user, date=(timestamp - datetime.timedelta(days=1)).date(),
                                                 intime__isnull=False)

            for att in atts:
                assert att.intime < timestamp, 'Intime can not be more that outtime'

                working_hours = (timestamp - att.intime).total_seconds()

                # working hours should be 7.5 hours
                if working_hours >= 27000:
                    att.type = 'PR' if att.type != 'LT' else 'LT'

                elif 27000 > working_hours:
                    att.type = 'LOP'

                att.outtime = timestamp
                att.working_hours = working_hours
                att.save()

    except Exception as error:
        print(traceback.format_exc())

conn.close()
