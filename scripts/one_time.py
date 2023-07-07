import os
import sys

sys.path.append('/opt/repos/DigikorePortal')

os.environ['DJANGO_SETTINGS_MODULE'] = 'DigikorePortal.settings'

import django

django.setup()
###########################################################

from base.models import *
from django.db.models import F

Shot.objects.update(parent_type='project', parent_id=F('project_id'))
