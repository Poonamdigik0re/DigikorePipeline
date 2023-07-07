import os
import sys

sys.path.append('/opt/repos/DigikorePortal')

os.environ['DJANGO_SETTINGS_MODULE'] = 'DigikorePortal.settings'

import django

django.setup()
###########################################################

from base.models import *

for profile in UserProfile.objects.filter(user__is_active=True, vehicle_number__isnull=False):
    vehicle_number = profile.vehicle_number.replace(' ', '').replace('-', '').replace('.', '')

    if len(vehicle_number) == 10:
        new_number = '{}-{}-{}'.format(vehicle_number[:4], vehicle_number[4:6], vehicle_number[6:])
    elif len(vehicle_number) == 9:
        new_number = '{}-{}-{}'.format(vehicle_number[:4], vehicle_number[5], vehicle_number[5:])
    else:
        new_number = vehicle_number

    if new_number:
        print(new_number)
        profile.vehicle_number = new_number
        profile.save()