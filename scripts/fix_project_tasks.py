import os
import sys

sys.path.append('/opt/repos/DigikorePortal')

os.environ['DJANGO_SETTINGS_MODULE'] = 'DigikorePortal.settings'

import django

django.setup()
###########################################################

from base.models import *

for task in Task.objects.all():
    if task.type not in task.project.default_tasks.all():
        task.project.default_tasks.add(task.type)
