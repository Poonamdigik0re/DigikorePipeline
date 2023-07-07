import os
import sys

sys.path.append('/opt/repos/DigikorePortal')

os.environ['DJANGO_SETTINGS_MODULE'] = 'DigikorePortal.settings'

import django

django.setup()
###########################################################

from base.models import *

DeliveryFormat(name='PC_Video', width=640, height=480, aspect_ratio=1.0)
DeliveryFormat(name='HD_720', width=1280, height=720, aspect_ratio=1.0)
DeliveryFormat(name='HD_1080', width=1920, height=1080, aspect_ratio=1.0)
DeliveryFormat(name='UHD_4K', width=3840, height=2160, aspect_ratio=1.0)
DeliveryFormat(name='1K_Super_35(full-ap)', width=1024, height=778, aspect_ratio=1.0)
DeliveryFormat(name='1K_Cinemascope', width=914, height=778, aspect_ratio=2.0)
DeliveryFormat(name='2K_Super_35(full-ap)', width=2048, height=1556, aspect_ratio=1.0)
DeliveryFormat(name='2K_Cinemascope', width=1828, height=1556, aspect_ratio=2.0)
DeliveryFormat(name='2K_DCP', width=2048, height=1080, aspect_ratio=1.0)
DeliveryFormat(name='4K_Super_35(full-ap)', width=4096, height=3112, aspect_ratio=1.0)
DeliveryFormat(name='4K_Cinemascope', width=3656, height=3112, aspect_ratio=2.0)
DeliveryFormat(name='4K_DCP', width=4096, height=2160, aspect_ratio=1.0)
DeliveryFormat(name='square_256', width=256, height=256, aspect_ratio=1.0)
DeliveryFormat(name='square_512', width=512, height=512, aspect_ratio=1.0)
DeliveryFormat(name='square_1K', width=1024, height=1024, aspect_ratio=1.0)
DeliveryFormat(name='square_2K', width=2048, height=2048, aspect_ratio=1.0)
DeliveryFormat(name='2K_LatLong', width=2048, height=1024, aspect_ratio=1.0)
DeliveryFormat(name='4K_LatLong', width=4096, height=2048, aspect_ratio=1.0)
DeliveryFormat(name='6K_LatLong', width=6144, height=3072, aspect_ratio=1.0)
DeliveryFormat(name='8K_LatLong', width=8192, height=4096, aspect_ratio=1.0)
DeliveryFormat(name='2K_CubeMap', width=2048, height=1536, aspect_ratio=1.0)
DeliveryFormat(name='4K_CubeMap', width=4096, height=3072, aspect_ratio=1.0)
DeliveryFormat(name='6K_CubeMap', width=6144, height=4608, aspect_ratio=1.0)
DeliveryFormat(name='8K_CubeMap', width=8192, height=6144, aspect_ratio=1.0)

# default project status
ProjectStatus(name='In Progress', default=True).save()
ProjectStatus(name='On Hold').save()
ProjectStatus(name='Complete').save()
ProjectStatus(name='Archived').save()

ProjectType(name='VFX', default=True).save()
ProjectType(name='Stereo').save()

# asset defaults
AssetStatus(name='Awaiting Assignment', bg_color='#e74c3c', fg_color='#ffffff', default=True).save()
AssetStatus(name='In Progress', bg_color="#2980b9", fg_color='#ffffff').save()
AssetStatus(name='Completed', bg_color='#4caf50', fg_color='#ffffff').save()

# shot defaults
ShotStatus(name='Awaiting Assignment', bg_color='#e74c3c', fg_color='#ffffff', default=True).save()
ShotStatus(name='In Progress', bg_color="#2980b9", fg_color='#ffffff').save()
ShotStatus(name='Completed', bg_color='#4caf50', fg_color='#ffffff').save()

# task defaults
TaskComplexity(name='Medium', bg_color='#1abc9c', fg_color='#ffffff', default=True).save()
TaskComplexity(name='Low', bg_color='#f1c40f', fg_color='#ffffff').save()
TaskComplexity(name='High', bg_color="#ff5722", fg_color="#ffffff").save()

TaskPriority(name='Medium', bg_color='#1abc9c', fg_color='#ffffff', default=True).save()
TaskPriority(name='Low', bg_color='#f1c40f', fg_color='#ffffff').save()
TaskPriority(name='High', bg_color="#ff5722", fg_color="#ffffff").save()

TaskStatus(name='Awaiting Assignment', bg_color='#e74c3c', fg_color='#ffffff', default=True).save()
TaskStatus(name='In Progress', bg_color="#2980b9", fg_color='#ffffff').save()
TaskStatus(name='Completed', bg_color='#4caf50', fg_color='#ffffff').save()

roto_dept = Department.objects.get(name='Roto')
paint_dept = Department.objects.get(name='Roto')
comp_dept = Department.objects.get(name='Comp')
depth_dept = Department.objects.get(name='Depth')

TaskType(name='Roto', department=roto_dept, default=True).save()
TaskType(name='Paint', department=paint_dept).save()
TaskType(name='Compositing', department=comp_dept).save()
TaskType(name='Depth', department=depth_dept).save()

SubtaskStatus(name='Awaiting Assignment', bg_color='#e74c3c', fg_color='#ffffff', default=True).save()
SubtaskStatus(name='In Progress', bg_color="#2980b9", fg_color='#ffffff').save()
SubtaskStatus(name='Completed', bg_color='#4caf50', fg_color='#ffffff').save()