import os
import sys

sys.path.append('/opt/repos/DigikorePortal')

os.environ['DJANGO_SETTINGS_MODULE'] = 'DigikorePortal.settings'

import django

django.setup()
###########################################################

from base.models import *
import datetime
import csv

from utils.celery import sendmail


def monthly_actuals_breakdown(*args, **kwargs):
    end_date = datetime.date.today().replace(day=25)
    start_date = (end_date - datetime.timedelta(days=30)).replace(day=26)

    # ACTUALS BREAKDOWN

    actuals_breakdown = f'/tmp/Monthly_Actuals_Breakdown_{end_date.strftime("%b_%Y")}.csv'
    writer = csv.writer(open(actuals_breakdown, 'w'))
    writer.writerow(['Empid', 'Username', 'Department', 'Designation', 'Date', 'Project', 'Project Type',
                     'Actuals (Days)'])

    values = ('actuals', 'date', 'project__name', 'project__type__name',
              'user__userprofile__full_name',
              'user__userprofile__empid',
              'user__userprofile__department__name',
              'user__userprofile__designation__name')

    for actual in BidActual.objects.filter(date__gte=start_date, date__lte=end_date).values(*values).order_by(
            'user_id', 'date'):
        writer.writerow([
            actual['user__userprofile__empid'],
            actual['user__userprofile__full_name'],
            actual['user__userprofile__department__name'],
            actual['user__userprofile__designation__name'],
            actual['date'],
            actual['project__name'],
            actual['project__type__name'],
            round(actual['actuals'] / 3600 / 8, 2)
        ])

    # ATTENDANCE BREAKDOWN

    attendance_breakdown = f'/tmp/Monthly_Attendance_Breakdown_{end_date.strftime("%b_%Y")}.csv'
    writer = csv.writer(open(attendance_breakdown, 'w'))
    writer.writerow(['Empid', 'Username', 'Department', 'Designation', 'Date', 'Hours', 'Days'])

    values = ('date', 'working_hours',
              'user__userprofile__full_name',
              'user__userprofile__empid',
              'user__userprofile__department__name',
              'user__userprofile__designation__name')

    for att in Attendance.objects.filter(date__gte=start_date, date__lte=end_date, working_hours__gt=0).values(*values):
        writer.writerow([
            att['user__userprofile__empid'],
            att['user__userprofile__full_name'],
            att['user__userprofile__department__name'],
            att['user__userprofile__designation__name'],
            att['date'],
            round(att['working_hours'] / 3600, 2),
            round(att['working_hours'] / 3600 / 8, 2)
        ])

    # SETUP EMAIL

    subject = f"Monthly Actuals / Attendance Breakdown : {end_date.strftime('%b %Y')}"
    message = "<p>Please find the attachment for Monthly Actuals Breakdown report.</p>"

    email_group = EmailGroup.objects.get(name='MONTHLY_ACTUALS_BREAKDOWN')
    mail_to = email_group.mail_to.split(';')
    cc_to = email_group.cc_to.split(';') if email_group.cc_to else []

    sendmail.delay(subject, message, mail_to, cc_to, attachments=[actuals_breakdown, attendance_breakdown])

    return True


if __name__ == "__main__":
    func = sys.argv[1]
    globals()[func](*sys.argv[2:])
