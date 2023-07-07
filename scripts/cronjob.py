import os
import sys

sys.path.append('/opt/repos/DigikorePortal')

os.environ['DJANGO_SETTINGS_MODULE'] = 'DigikorePortal.settings'

import django

django.setup()
###########################################################

from base.models import *

from django.db.models import Q
import subprocess
import re
import datetime
from utils import connect_mongo, connect_msi_pnq, seconds_to_time

mongo_db = connect_mongo()
license_usage = mongo_db.license_usage

# clear the table
license_usage.drop()

foundry_servers = {
    '4101@pnq-lic-foundry01.digikore.work': [
        {'name': 'nuke_i', 'version': 'v2019.0322', 'title': 'Nuke',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
        {'name': 'nuke_r', 'version': 'v2019.0322', 'title': 'Nuke Render',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
        {'name': 'nukex_i', 'version': 'v2019.0322', 'title': 'Nuke-X',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
        {'name': 'nukexassist_i', 'version': 'v2019.0322', 'title': 'Nuke-X Assist',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
        {'name': 'nukestudio_i', 'version': 'v2019.0322', 'title': 'Nuke Studio',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
    ],
    '4101@pnq-lic-foundry02.digikore.work': [
        {'name': 'nuke_i', 'version': 'v2019.0322', 'title': 'Nuke',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
    ],
    '4101@lic-foundry.lfilms.net': [
        {'name': 'nuke_i', 'version': 'v2018.0322', 'title': 'Nuke',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
        {'name': 'nukex_i', 'version': 'v2018.0322', 'title': 'NukeX',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
        {'name': 'nukestudio_i', 'version': 'v2018.0322', 'title': 'Nuke Studio',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},

        {'name': 'caravr_nuke_r', 'version': 'v1.0', 'title': 'Cara VR Nuke Render',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
        {'name': 'caravr_nuke_i', 'version': 'v1.0', 'title': 'Cara VR Nuke Plugin',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
        {'name': 'ocula_nuke_r', 'version': 'v4.0', 'title': 'Ocula Nuke Render',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
        {'name': 'ocula_nuke_i', 'version': 'v4.0', 'title': 'Ocula Nuke Plugin',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
    ]
}

silhouette_servers = {
    '4313@pun-sfx.digikore.work': [
        {'name': 'silhouette', 'version': 'v6.0', 'title': 'Silhouette v6.0',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
        {'name': 'mocha', 'version': 'v6.0', 'title': 'Mocha v6.0',
         'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []}
    ]
}


# foundry_servers = {
#     '4101@lya-lic-foundry.digikore.work': [
#         {'name': 'nuke_i', 'version': 'v2019.0322', 'title': 'Nuke',
#          'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
#     ],
# }
#
# silhouette_servers = {
#     '4313@lya-lic-sfx.digikore.work': [
#         {'name': 'silhouette', 'version': 'v6.0', 'title': 'Silhouette v6.0',
#          'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []},
#         {'name': 'mocha', 'version': 'v6.0', 'title': 'Mocha v6.0',
#          'count': 0, 'inuse': 0, 'reserve': 0, 'expire': '', 'users': []}
#     ]
# }


def add_paid_leaves():
    today = datetime.date.today() - datetime.timedelta(days=1)
    doj_limit = today.replace(day=20)
    garga = User.objects.get(username='garga')

    for user in User.objects.filter(is_active=True,
                                    userprofile__location__name='pnq',
                                    userprofile__date_of_joining__lte=doj_limit):
        user.userprofile.paid_leave = user.userprofile.paid_leave + 1
        user.userprofile.casual_leave = user.userprofile.casual_leave + 1
        user.userprofile.save()

        LeaveLog(user=user, leave_type='paid_leave', total_days=1, created_by=garga,
                 comment="Added paid-leave for the month of %s" % today.strftime("%b-%Y")).save()

        LeaveLog(user=user, leave_type='casual_leave', total_days=1, created_by=garga,
                 comment="Added casual-leave for the month of %s" % today.strftime("%b-%Y")).save()

    return True


def mark_absent():
    now = datetime.datetime.now()
    today = now.date()
    shift = None

    if now.hour == 9:
        shift = 'Morning'
    elif now.hour == 21:
        shift = 'Night'

    if today.isoweekday() not in [6, 7] and CompanyHoliday.objects.filter(date=today,
                                                                          working=False).count() == 0 and shift:
        for team in Team.objects.filter(shift__name=shift):
            for member in team.members.all():
                if Attendance.objects.filter(user=member, date=today).count() == 0:
                    Attendance(user=member, date=today, type='LOP').save()

    return True


def mark_absent_all():
    end_date = datetime.date.today()
    start_date = (end_date - datetime.timedelta(days=32)).replace(day=26)

    for x in range((end_date - start_date).days):
        date = start_date + datetime.timedelta(days=x)
        if date.isoweekday() not in [6, 7] and CompanyHoliday.objects.filter(date=date, working=False).count() == 0:
            for user in User.objects.filter(userprofile__location__name='pnq',
                                            userprofile__date_of_joining__lte=date).exclude(
                userprofile__date_of_leaving__lte=date):
                if Attendance.objects.filter(user=user, date=date).count() == 0:
                    Attendance(user=user, date=date, type='LOP').save()

    return True


def in_only_absent():
    yesterday = datetime.date.today() - datetime.timedelta(days=1)

    filters = {'userprofile__location__name': 'pnq', 'userprofile__date_of_joining__lte': yesterday}
    exclude = {'userprofile__date_of_leaving__lte': yesterday}

    for user in User.objects.filter(**filters).exclude(**exclude):
        for att in Attendance.objects.filter(user=user, date=yesterday, outtime__isnull=True):
            att.type = 'LOP'
            att.save()

    return True


def mark_compoff():
    date = datetime.date.today() - datetime.timedelta(days=1)
    exclude_date = datetime.date(2019, 1, 27)

    # employees who exceeded 16 hours
    for att in Attendance.objects.exclude(date=exclude_date).filter(date=date, working_hours__range=(57600, 86400)):
        working_hours = "{0:02d}:{1:02d}:{2:02d}".format(*seconds_to_time(att.working_hours))

        CompOff(user=att.user, date=att.date, total_days=1,
                reason="Worked for more than 16 Hours (%s)" % working_hours).save()

    # employees working on weekends or holidays
    if date.isoweekday() in [6, 7] or Holiday.objects.filter(date=date).count() > 0:
        for att in Attendance.objects.exclude(date=exclude_date).filter(date=date, type__in=['PR', 'IN']):
            CompOff(user=att.user, date=att.date, total_days=1, can_be_incentive=True,
                    reason="Worked on weekend/holiday, %s" % date.strftime('%a %b %d, %Y')).save()


def rlmstat(license_server):
    for server, apps in license_server.items():

        process = subprocess.Popen(['/opt/repos/bin/rlmutil', 'rlmstat', '-a', '-c', server],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        output, error = process.communicate()

        lines = output.split(b'\n')

        for app in apps:
            users = []

            for i, v in enumerate(lines):
                user_search = re.search('{0} {1}: (\w+)@([\w\d-]+)'.format(app['name'], app['version']),
                                        v.decode('utf-8'))

                # search for users
                if user_search:
                    username, workstation = user_search.groups()
                    user_work = '%s@%s' % (username, workstation)

                    if user_work not in users:
                        users.append(user_work)
                        app['users'].append({'username': username, 'workstation': workstation})

                # search for other attributes
                if re.search('{0} {1}$'.format(app['name'], app['version']), v.decode('utf-8')):
                    search = re.search('count: (\d+), # reservations: (\d+), inuse: (\d+), exp: ([\w\d-]+)',
                                       lines[i + 1].decode('utf-8'))
                    if search:
                        count, reserve, inuse, expire = search.groups()
                        app['count'] += int(count)
                        app['reserve'] += int(reserve)
                        app['inuse'] += int(inuse)
                        app['expire'] = expire

            app['server'] = server
            app['timestamp'] = datetime.datetime.now()

            license_usage.insert_one(app)


def get_license_usage():
    rlmstat(silhouette_servers)
    rlmstat(foundry_servers)


def sync_msi():
    conn = connect_msi_pnq()
    cursor = conn.cursor()

    values = ['designation__name', 'department__name', 'team__lead__username', 'user__username']

    for user in UserProfile.objects.filter(location__name='pnq',
                                           user__is_active=True, team__isnull=False).values(*values):
        cursor.execute(
            """UPDATE login SET (title, department, lead, approver) = (%(title)s, %(department)s, %(lead)s, %(approver)s) WHERE login=%(login)s""",
            {"login": user['user__username'],
             "title": user['designation__name'],
             "department": user['department__name'],
             "lead": user['team__lead__username'],
             "approver": user['team__lead__username']})

    for user in User.objects.filter(userprofile__location__name='pnq',
                                    is_active=False).values_list('username', flat=True):
        cursor.execute("""UPDATE login SET s_status='retired' WHERE login=%(login)s""", {"login": user})

    conn.commit()
    conn.close()

    return True


def annual_leave_lapse():
    today = datetime.date.today()
    garga = User.objects.get(username='garga')

    for user in User.objects.filter(userprofile__location__name='pnq'):
        casual_leave = user.userprofile.casual_leave

        user.userprofile.casual_leave = 0
        user.userprofile.save()

        LeaveLog(user=user, leave_type='casual_leave', total_days=casual_leave * -1, created_by=garga,
                 comment="Casual leaves lapsed for the year %s" % today.year).save()

    return True


def update_resource_cache():
    date = datetime.date.today()
    location = Location.objects.get(id='pnq')

    for department in Department.objects.all():
        cache = ResourceCache(department=department, date=date)

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

    return True


if __name__ == "__main__":
    func = sys.argv[1]
    globals()[func]()
