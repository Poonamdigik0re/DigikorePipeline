import os
import sys

sys.path.append('/opt/repos/DigikorePortal')

os.environ['DJANGO_SETTINGS_MODULE'] = 'DigikorePortal.settings'

import django

django.setup()
###########################################################

from base.models import *
import re
import datetime
import traceback

import psycopg2

from utils.celery import sendmail


def archive_project(project_name):
    include_snapshot = ('Client Approved', 'Approved', 'Complete', 'Dept Approved', 'Final')
    exclude_snapshot = ('DAILIES', 'CLIENT', 'DELIVERY')
    exclude_shot = ('Omit', 'Not Turned Over')

    project_root = '/digi/prod/Projects/FEATURE'
    backup_root = '/digi/prod/Projects/BACKUP'

    def hard_link(source_dir, dest_dir, f_name):
        src_path = os.path.join(source_dir, f_name)
        dst_path = os.path.join(dest_dir, f_name)
        f_size = 0

        if not os.path.exists(src_path):
            return f_size

        if os.path.exists(dst_path):
            f_size = os.path.getsize(dst_path)
            return f_size

        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        os.link(src_path, dst_path)
        f_size = os.path.getsize(dst_path)

        return f_size

    def process_file_range(source_dir, dest_dir, f_name):
        f_size = 0
        pattern = re.sub('%.*', '', f_name)

        if os.path.exists(source_dir):
            for f_name in os.listdir(source_dir):
                if re.search(pattern, f_name):
                    f_size += hard_link(source_dir, dest_dir, f_name)

        return f_size

    def backup_support_files():
        f_size = 0
        for dir_name in ['2_PROD', '3_RND', '4_REF', 'attachments', 'NOTE_ATTACHMENTS']:
            for source_dir, folds, files in os.walk(os.path.join(project_root, project_name, dir_name)):
                for f_name in files:
                    dest_dir = source_dir.replace(project_root, backup_root)
                    f_size += hard_link(source_dir, dest_dir, f_name)

        return f_size

    try:
        conn = psycopg2.connect(host="pnq-db01.digikore.work", dbname="sthpw", user="postgres", password="")
        cursor = conn.cursor()

        query = f"""SELECT file.relative_dir, file.file_name FROM file WHERE file.snapshot_code IN (
            -- Select the main snapshots
            SELECT DISTINCT snapshot.record_code from shot, snapshot
                WHERE snapshot.status IN {include_snapshot}
                    AND snapshot.process NOT IN {exclude_snapshot}
                    AND shot.shot_status NOT IN {exclude_shot}
                    AND shot.record_code = snapshot.parent_record_code
                    AND snapshot.project_code = '{project_name}'
            -- Select the first level dependencies
            UNION SELECT DISTINCT snapshot_to_snapshot.child_snapshot_code from snapshot_to_snapshot
                WHERE snapshot_to_snapshot.parent_snapshot_code IN (
                    SELECT DISTINCT snapshot.record_code from shot, snapshot
                        WHERE snapshot.status IN {include_snapshot}
                            AND snapshot.process NOT IN {exclude_snapshot}
                            AND shot.shot_status NOT IN {exclude_shot}
                            AND shot.record_code = snapshot.parent_record_code
                            AND snapshot.project_code = '{project_name}'
                )
            -- Select the second level dependencies
            UNION SELECT DISTINCT snapshot_to_snapshot.child_snapshot_code from snapshot_to_snapshot
                WHERE snapshot_to_snapshot.parent_snapshot_code in(
                    SELECT DISTINCT snapshot_to_snapshot.child_snapshot_code from snapshot_to_snapshot
                        WHERE snapshot_to_snapshot.parent_snapshot_code IN (
                            SELECT DISTINCT snapshot.record_code from shot, snapshot
                                WHERE snapshot.status IN {include_snapshot}
                                    AND snapshot.process NOT IN {exclude_snapshot}
                                    AND shot.shot_status NOT IN {exclude_shot}
                                    AND shot.record_code = snapshot.parent_record_code
                                    AND snapshot.project_code = '{project_name}') 
                )
        );"""

        cursor.execute(query)
        archive_size = 0

        for line in cursor.fetchall():
            file_dir, file_name = line

            # when files are published from windows
            file_dir.replace('L:/Projects/FEATURE/', '')

            src_dir = os.path.join(project_root, file_dir)
            dst_dir = os.path.join(backup_root, file_dir)

            if not file_dir or not file_name:
                continue

            if re.search("[~.]$", file_name):
                continue

            if re.search('%\d+', file_name):
                archive_size += process_file_range(src_dir, dst_dir, file_name)
            else:
                archive_size += hard_link(src_dir, dst_dir, file_name)

        # Archive the support files and folders
        archive_size += backup_support_files()

        try:
            # update status
            project = Project.objects.name(id=project_name)
            project.status = ProjectStatus.objects.get(name='Archived')
            project.archive_size = archive_size
            project.archive_completed_on = datetime.datetime.now()
            project.save()
        except:
            pass

        # send email and update the status
        email_group = EmailGroup.objects.get(name='PROJECT_ARCHIVAL')
        mail_to = email_group.mail_to.split(';')
        cc_to = email_group.cc_to.split(';') if email_group.cc_to else []
        message = f"""<p style='white-space: pre-line'>
        Hi Team,

        <b>{project_name}</b> is now archived.
        </p>
        """

        sendmail.delay(f'PROJECT ARCHIVAL: {project_name}', message, mail_to, cc_to)

    except Exception:
        # Project.objects.filter(id=project_id).update(status=ProjectStatus.objects.get(name='Ready for Archival'))

        message = f"""<p style='white-space: pre-line'>{traceback.format_exc()}</p>"""

        sendmail.delay(f'PROJECT ARCHIVAL FAILED: {project_name}', message, ['development@digikore3d.com'],
                       ['io_tech@digikore3d.com', 'pnq_io@digikore.work'])
