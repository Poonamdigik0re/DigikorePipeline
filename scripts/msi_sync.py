import os
import sys

sys.path.append('/opt/repos/DigikorePortal')

os.environ['DJANGO_SETTINGS_MODULE'] = 'DigikorePortal.settings'

import django

django.setup()
###########################################################

from base.models import *
import psycopg2

conn = psycopg2.connect(host="pnq-db01.digikore.work", dbname="sthpw", user="postgres", password="")
cursor = conn.cursor()

garga = User.objects.get(username='garga')

task_types = {
    'rot': 'roto',
    'pnt': 'paint',
    'cmp': 'comp',
    'dpt': 'depth',
    'edt': 'editorial',
    'prd': 'prod',
    'elmqc': 'elementqc',
    'mm': 'matchmove',
    'dmp': 'matte_paint',
    'lgt': 'lighting',
    'mdl': 'modeling',
    'anm': 'animation',
    'tex': 'texturing',
    'rig': 'rigging',
    'lyt': 'lighting',
}

task_statuses = {
    'na': 'Not Applicable',
    'Not Required': 'Not Applicable',
    'in_progress': 'In Progress',
    'Completed': 'Final',
    'QC Fail': 'TQC Kickback',
}

note_task_types = TaskType.objects.values_list('name', flat=True)
note_type = NoteType.objects.get(default=True)

for project in Project.objects.filter(msi_sync=True, status__name='In Progress').values('id', 'name'):

    ######################################################
    # SYNC SHOTS
    ######################################################

    query = f"""select code, sequence_code, reel, shot_status, received_ff, received_lf, working_ff, working_lf, source_status, source_type, record_code 
    from shot 
    where project_code='{project['name'].upper()}' 
    and sequence_code is not null
    and sequence_code != 'na'"""
    cursor.execute(query)

    for line in cursor.fetchall():
        shot_name, sequence_name, reel, shot_status_name, client_ff, client_lf, working_ff, working_lf, source_status, source_type, record_code = line

        shot_status = ShotStatus.objects.get_or_create(name=shot_status_name)[0]
        shot = Shot.objects.filter(project_id=project['id'],
                                   sequence=sequence_name,
                                   parent_type='project',
                                   parent_id=project['id'],
                                   name=shot_name).first()

        client_first_frame = int(client_ff) if client_ff else 0
        client_last_frame = int(client_lf) if client_lf else 0
        working_first_frame = int(working_ff) if working_ff else 0
        working_last_frame = int(working_lf) if working_lf else 0

        if shot:
            shot.msi_record_code = record_code
            shot.client_first_frame = client_first_frame if client_first_frame else 0
            shot.client_last_frame = client_last_frame if client_last_frame else 0
            shot.working_first_frame = working_first_frame if working_first_frame else 0
            shot.working_last_frame = working_last_frame if working_last_frame else 0
            shot.status = shot_status
            shot.reel = reel

            shot.save()

        else:
            shot = Shot(project_id=project['id'], parent_type='project', parent_id=project['id'],
                        name=shot_name,
                        status=shot_status,
                        client_first_frame=client_first_frame,
                        client_last_frame=client_last_frame,
                        working_first_frame=working_first_frame,
                        working_last_frame=working_last_frame,
                        reel=reel,
                        sequence=sequence_name,
                        msi_record_code=record_code,
                        created_by=garga)
            shot.save()

    ######################################################
    # SYNC TASKS
    ######################################################

    query = f"""SELECT shot.code, shot.sequence_code, task.status, task.process, task.context, task.complexity, task.start_date, task.eta, task.client_bid, task.lead_bid, task.bid_name, task.lead_assigned, task.assigned, task.record_code
    FROM task, shot 
    WHERE task.project_code='{project['name'].upper()}'
    AND task.process NOT IN ('dev', 'rnd') 
    AND task.sub_task IS NULL 
    AND task.s_status IS NULL 
    AND (task.lead_assigned IS NULL OR task.lead_assigned != 'digikore_lya')
    AND (task.assigned IS NULL OR task.assigned != 'digikore_lya') 
    AND task.parent_record_code=shot.record_code 
    AND shot.sequence_code IS NOT NULL
    AND shot.sequence_code != 'na';"""
    cursor.execute(query)

    for line in cursor.fetchall():
        try:
            shot_name, sequence_name, task_status, task_type, task_name, task_complexity, task_start_date, task_eta, client_bids, lead_bids, turnover_code, lead_assignee, task_assignee, record_code = line

            shot = Shot.objects.filter(project_id=project['id'], parent_type='project', parent_id=project['id'],
                                       name=shot_name, sequence=sequence_name).first()

            if shot:
                _status_name = task_statuses[task_status] if task_status in task_statuses else task_status
                task_status = TaskStatus.objects.get_or_create(name=_status_name)[0]
                _type_name = task_types[task_type] if task_type in task_types.keys() else task_type
                task_type = TaskType.objects.get(name=_type_name)

                client_bids = client_bids if client_bids else 0
                lead_bids = lead_bids if lead_bids else 0

                lead_assignee = User.objects.get(username=lead_assignee) if lead_assignee else None
                priority = TaskPriority.objects.get(default=True)

                if task_complexity:
                    complexity = TaskComplexity.objects.get_or_create(name=task_complexity.lower())[0]
                else:
                    complexity = TaskComplexity.objects.get(default=True)

                task = Task.objects.filter(project_id=project['id'], parent_type='shot', parent_id=shot.id,
                                           type=task_type, name=task_name).first()

                if task:
                    task.msi_record_code = record_code
                    task.status = task_status
                    task.complexity = complexity
                    task.assignee = lead_assignee
                    task.bids = client_bids
                    # task.turnover_code = turnover_code
                    task.start_date = task_start_date
                    task.end_date = task_eta
                    task.working_first_frame = shot.working_first_frame
                    task.working_last_frame = shot.working_last_frame
                    task.save()
                else:
                    task = Task(project_id=project['id'], parent_type='shot', parent_id=shot.id,
                                type=task_type, status=task_status, name=task_name, complexity=complexity,
                                priority=priority, assignee=lead_assignee, bids=client_bids,
                                start_date=task_start_date, end_date=task_eta,
                                working_first_frame=shot.working_first_frame,
                                working_last_frame=shot.working_last_frame,
                                msi_record_code=record_code)
                    task.save()

                _subtask_status = task_statuses[task_status] if task_status in task_statuses else task_status
                subtask_status = SubtaskStatus.objects.get_or_create(name=_subtask_status)[0]
                assignee = User.objects.get(username=task_assignee) if task_assignee else None

                subtask = Subtask.objects.filter(project_id=project['id'], parent_type='task',
                                                 parent_id=task.id, name=task_name).first()

                if subtask:
                    subtask.status = subtask_status
                    subtask.assignee = assignee
                    subtask.bids = lead_bids
                else:
                    subtask = Subtask(project_id=project['id'], parent_type='task', parent_id=task.id,
                                      bids=lead_bids, name=task_name, status=subtask_status, assignee=assignee)

                subtask.save()

        except Exception as error:
            print(line)
            print(error)

    ######################################################
    # SYNC SUBTASKS
    ######################################################

    query = f"""SELECT shot.code, shot.sequence_code, task.status, task.process, task.context, task.assigned, task.sub_task, task.lead_bid
        FROM task, shot 
        WHERE task.project_code='{project['name'].upper()}'
        AND task.sub_task IS NOT NULL 
        AND task.s_status IS NULL 
        AND task.process NOT IN ('dev', 'rnd')
        AND (task.lead_assigned IS NULL OR task.lead_assigned != 'digikore_lya')
        AND (task.assigned IS NULL OR task.assigned != 'digikore_lya')
        AND task.parent_record_code=shot.record_code 
        AND shot.sequence_code IS NOT NULL
        AND shot.sequence_code != 'na';"""
    cursor.execute(query)

    for line in cursor.fetchall():
        try:
            shot_name, sequence_name, task_status, task_type, task_name, task_assignee, subtask_name, lead_bids = line

            shot = Shot.objects.filter(project_id=project['id'], parent_type='project', parent_id=project['id'],
                                       sequence=sequence_name, name=shot_name).first()

            if shot:
                task_type_name = task_types[task_type] if task_type in task_types.keys() else task_type

                task = Task.objects.filter(project_id=project['id'], parent_type='shot', parent_id=shot.id,
                                           type__name=task_type_name, name=task_name).first()

                if task:
                    subtask_status_name = task_statuses[task_status] if task_status in task_statuses else task_status
                    subtask_status = SubtaskStatus.objects.get_or_create(name=subtask_status_name)[0]
                    assignee = User.objects.get(username=task_assignee) if task_assignee else None

                    subtask = Subtask.objects.filter(project_id=project['id'], parent_type='task',
                                                     parent_id=task.id, name=subtask_name).first()

                    lead_bids = lead_bids if lead_bids else 0

                    if subtask:
                        subtask.status = subtask_status
                        subtask.assignee = assignee
                        subtask.bids = lead_bids
                        subtask.save()
                    else:
                        subtask = Subtask(project_id=project['id'], parent_type='task', parent_id=task.id,
                                          bids=lead_bids, name=subtask_name, status=subtask_status,
                                          assignee=assignee)
                        subtask.save()

        except Exception as error:
            print(line)
            print(error)
