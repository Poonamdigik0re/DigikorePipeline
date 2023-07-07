import os
import sys

from django.db.models import Sum

sys.path.append('/opt/repos/DigikorePortal')

os.environ['DJANGO_SETTINGS_MODULE'] = 'DigikorePortal.settings'

import django

django.setup()
###########################################################

from base.models import *
import psycopg2

conn = psycopg2.connect(host="pnq-db01.digikore.work", dbname="sthpw", user="postgres", password="")
cursor = conn.cursor()

for project in Project.objects.filter(msi_sync=True, status__name="In Progress").values('id', 'name'):
    query = "select record_code from task where project_code='%s'" % project['name']

    cursor.execute(query)

    msi_codes = [x[0] for x in cursor.fetchall()]

    for task in Task.objects.filter(project_id=project['id']).values('id', 'msi_record_code'):
        if task['msi_record_code'] in msi_codes:
            msi_codes.remove(task['msi_record_code'])
        else:
            actuals = BidActual.objects.filter(task_id=task['id']).aggregate(Sum('actuals'))['actuals__sum']

            if actuals == 0:
                BidActual.objects.filter(task_id=task['id']).delete()
                Task.objects.filter(id=task['id']).delete()
            elif actuals is None:
                Task.objects.filter(id=task['id']).delete()
            else:
                print(project['name'], round(actuals / 3600 / 8, 2) if actuals and actuals > 0 else 0)
