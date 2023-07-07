import os
import sys

sys.path.append('/opt/repos/DigikorePortal')

os.environ['DJANGO_SETTINGS_MODULE'] = 'DigikorePortal.settings'

import django

django.setup()
###########################################################

from base.models import *
import re

import psycopg2


def archive_dependencies(snapshot_code, backup_root):
    project_root = '/digi/prod/Projects/FEATURE'

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

        # os.link(src_path, dst_path)
        # f_size = os.path.getsize(dst_path)
        print(dst_path)

        return f_size

    def process_file_range(source_dir, dest_dir, f_name):
        f_size = 0
        pattern = re.sub('%.*', '', f_name)

        if os.path.exists(source_dir):
            for f_name in os.listdir(source_dir):
                if re.search(pattern, f_name):
                    f_size += hard_link(source_dir, dest_dir, f_name)

        return f_size

    try:
        conn = psycopg2.connect(host="pnq-db01.digikore.work", dbname="sthpw", user="postgres", password="")
        cursor = conn.cursor()

        query = f"""SELECT file.relative_dir, file.file_name FROM file WHERE file.base_type='sequence' AND file.snapshot_code IN (
          -- Select the main snapshots
          SELECT DISTINCT snapshot.record_code from shot, snapshot
              WHERE snapshot.record_code='{snapshot_code}'
                  AND shot.record_code = snapshot.parent_record_code
          -- Select the first level dependencies
          UNION SELECT DISTINCT snapshot_to_snapshot.child_snapshot_code from snapshot_to_snapshot
              WHERE snapshot_to_snapshot.parent_snapshot_code IN (
                  SELECT DISTINCT snapshot.record_code from shot, snapshot
                      WHERE snapshot.record_code='{snapshot_code}'
                          AND shot.record_code = snapshot.parent_record_code
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

        print(archive_size)

    except Exception as error:
        print(error)


archive_dependencies('SNAPSHOT0005575067PNQ',
                     '/digi/prod/Projects/FEATURE/GDY_628/0_DELIVERABLES/DLV/DLV_GDY_628_20190911B/LEG_20190911B/GDY_Part_01_prep_20190911/ICDN_BOR_0120_bg01_v01_v1_prep_v8/Dependencies')
