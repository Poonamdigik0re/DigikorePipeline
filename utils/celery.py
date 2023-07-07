import asyncio
import datetime
import json
import os
import re
import shutil
import smtplib
import subprocess
import sys
import traceback
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import ldap3
import psycopg2
import websockets
from celery import Celery
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

sys.path.append('/opt/repos/DigikorePortal')

os.environ['DJANGO_SETTINGS_MODULE'] = 'DigikorePortal.settings'

import django

django.setup()
###########################################################


from DigikorePortal.settings import FOLDERS
from base.models import *

rabbitmq_user = CONFIG['rabbitmq']['user']
rabbitmq_pass = CONFIG['rabbitmq']['password']
rabbitmq_vhost = CONFIG['rabbitmq']['vhost']

# app = Celery('utils',
#              broker=f'amqp://{rabbitmq_user}:{rabbitmq_pass}@{rabbitmq_vhost}:15672/{rabbitmq_vhost}',
#              # backend=f'amqp://{rabbitmq_user}:{rabbitmq_pass}@localhost:5672/{rabbitmq_vhost}',
#              )
#
# app.conf.update(
#     result_expires=3600
# )

app = Celery('DigikorePortal')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# SERVICE_ACCOUNT_JSON_FILE_PATH = '/opt/repos/creds.json'


def connect_ldap():
    server = ldap3.Server(CONFIG['ldap']['server'], use_ssl=True)
    connection = ldap3.Connection(server, auto_bind=True, user=CONFIG['ldap']['user'],
                                  password=CONFIG['ldap']['password'], authentication=ldap3.NTLM)

    return connection


@app.task
def create_project_group(name, gid):
    ldap_conn = connect_ldap()

    group_name = f'prj-{name.lower()}'
    attrs = {
        "sAMAccountName": group_name,
        "name": group_name,
        "cn": group_name,
        "description": f"GID: {gid}",
        "gidNumber": gid
    }

    group_dn = CONFIG['ldap']['group_cn'].format(name=group_name)
    ldap_conn.add(group_dn, 'group', attrs)

    return True


@app.task
def create_ldap_group(group_name, gid):
    ldap_conn = connect_ldap()

    attrs = {
        "sAMAccountName": group_name,
        "name": group_name,
        "cn": group_name,
        "description": f"GID: {gid}",
        "gidNumber": gid
    }

    group_dn = CONFIG['ldap']['group_cn'].format(name=group_name)
    ldap_conn.add(group_dn, 'group', attrs)

    return True


@app.task
def update_ldap_group(users, group, remove=False):
    """
    users : UserProfile - full_name, location__name

    # clear existing groups
    ldap_conn.search(user_dn, '(&(objectclass=person))', attributes=['memberOf'])
    ldap_conn.extend.microsoft.remove_members_from_groups(user_dn, list(ldap_conn.entries[0].memberof))
    """
    ldap_conn = connect_ldap()

    for user in users:
        user_cn = CONFIG['ldap']['user_cn'].format(name=user['full_name'], location=user['location__name'])
        group_cn = CONFIG['ldap']['group_cn'].format(name=group)

        if remove:
            ldap_conn.extend.microsoft.remove_members_from_groups(user_cn, group_cn)
        else:
            ldap_conn.extend.microsoft.add_members_to_groups(user_cn, group_cn)

    return True


@app.task
def unlock_ldap_account(name, location):
    ldap_conn = connect_ldap()
    try:
        user_dn = CONFIG['ldap']['user_cn'].format(name=name, location=location)

        # disable user
        ldap_conn.extend.microsoft.unlock_account(user_dn)

    except Exception as error:
        print(traceback.format_exc())

    return True


@app.task
def reset_ldap_account(name, location):
    ldap_conn = connect_ldap()
    try:
        user_dn = CONFIG['ldap']['user_cn'].format(name=name, location=location)

        ldap_conn.extend.microsoft.modify_password(user_dn, CONFIG['ldap']['default_password'])

    except Exception as error:
        print(traceback.format_exc())

    return True


@app.task
def sendmail(subject, message, mail_to, cc_to, reply_to=None, attachments=[]):
    msg = MIMEMultipart()

    msg['From'] = CONFIG['smtp']['from']
    msg['To'] = ', '.join(mail_to)
    msg['Cc'] = ', '.join(cc_to)
    msg['Subject'] = subject

    if reply_to:
        msg.add_header('reply-to', reply_to)

    for attachment in attachments:
        _, file_name = os.path.split(attachment)

        payload = MIMEBase('application', 'octet-stream')
        payload.set_payload(open(attachment, 'rb').read())
        encoders.encode_base64(payload)

        payload.add_header('Content-Disposition', f'attachment; filename= {file_name}')

        msg.attach(payload)

    msg.attach(MIMEText(message, 'html'))

    s = smtplib.SMTP(CONFIG["smtp"]['host'], CONFIG['smtp']['port'])

    s.login(CONFIG['smtp']['username'], CONFIG['smtp']['password'])
    s.sendmail(msg['From'], mail_to + cc_to, msg.as_string())
    s.quit()

    return True


@app.task
def save_change_log(project_id, model_type, model_id, key, value, user_id):
    if key not in ['parent_type', 'parent_id', 'project_id']:
        model_name = model_type.title()

        if key.endswith('_id'):
            key = key.replace('_id', '')
            if key in ['assignee']:
                value = User.objects.get(id=value).username
            else:
                key_class = globals()[model_name + key.title()]
                value = key_class.objects.get(id=value).name

        ChangeLog(project_id=project_id, parent_type=model_type, parent_id=model_id,
                  key=key, value=value, created_by_id=user_id).save()

        # update msi
        if model_type == 'task':
            if key.endswith('_id'):
                key = key.replace('_id', '')
                if key in ['assignee']:
                    value = User.objects.get(id=value).username
                else:
                    key_class = globals()[model_name + key.title()]
                    value = key_class.objects.get(id=value).name

            # todo: enable this later
            # msi_record_code = Task.objects.get(id=model_id).msi_record_code
            # update_msi_task(msi_record_code, key, value)

    return True


@app.task
def wss_publish(path, data):
    print("*",path)
    print("*", data)
    async def send():
        async with websockets.connect('ws://127.0.0.1:8101/' + path) as websocket:
            message = json.dumps({"func": "wss_publish", "data": data})
            await websocket.send(message)

    asyncio.get_event_loop().run_until_complete(send())


@app.task
def create_client_signiant_folder(client_name):
    client_name = re.sub('\W', '_', client_name)

    os.makedirs(f'/digi/signiant/{client_name}', 0o770)
    os.makedirs(f'/digi/signiant/{client_name}/bidding', 0o770)

    return True


@app.task
def create_project_signiant_folder(client_name, project_name):
    client_name = re.sub('\W', '_', client_name)

    os.makedirs(f'/digi/signiant/{client_name}/{project_name}', 0o770)
    os.makedirs(f'/digi/signiant/{client_name}/{project_name}/from_digikore', 0o770)
    os.makedirs(f'/digi/signiant/{client_name}/{project_name}/to_digikore', 0o770)

    return True


@app.task
def create_folder(model_type, model_id):
    def create_project_folder(project_id):
        project = Project.objects.get(id=project_id)
        project_path = FOLDERS['project']['path'].format(root_project=FOLDERS['root']['project'], name=project.name)

        if not os.path.exists(project_path):
            os.makedirs(project_path, int(FOLDERS['project']['chmod'], 8))
            os.chown(project_path, 0, project.gid)

        for x in FOLDERS['project']['extras']:
            path = x['path'].format(project_path=project_path)

            if not os.path.exists(path):
                os.makedirs(path, int(x['chmod'], 8))

        return project_path

    def create_shot_folder(shot_id):
        shot = Shot.objects.get(id=shot_id)
        shot_path = FOLDERS['shot']['path'].format(name=shot.name)

        if not os.path.exists(shot_path):
            os.makedirs(shot_path, int(FOLDERS['shot']['chmod'], 8))

        for x in FOLDERS['shot']['extras']:
            path = x['path'].format(shot_path=shot_path)

            if not os.path.exists(path):
                os.makedirs(path, int(x['chmod'], 8))

        return shot_path

    def create_task_folder(task_id):
        task = Task.objects.get(id=task_id)

        if task.parent_type == 'shot':
            shot_path = create_shot_folder(task.parent_id)
            task_path = FOLDERS['shot_task']['path'].format(shot_path=shot_path, name=task.name)

            if not os.path.exists(task_path):
                os.makedirs(task_path, int(FOLDERS['shot_task']['chmod'], 8))

            for x in FOLDERS['shot_task']['extras']:
                path = x['path'].format(task_path=task_path)

                if not os.path.exists(path):
                    os.makedirs(path, int(x['chmod'], 8))

            return task_path

    def create_subtask_folder(subtask_id):
        subtask = Subtask.objects.get(id=subtask_id)

        task_path = create_task_folder(subtask.parent_id)
        subtask_path = FOLDERS['subtask']['path'].format(task_path=task_path, name=subtask.name)

        if not os.path.exists(subtask_path):
            os.makedirs(subtask_path, int(FOLDERS['subtask']['chmod'], 8))
            os.chmod(subtask_path, 0, CONFIG['ldap']['group_gid'])

        for x in FOLDERS['subtask']['extras']:
            path = x['path'].format(subtask_path=subtask_path)

            if not os.path.exists(path):
                os.makedirs(path, int(x['chmod'], 8))
                os.chmod(path, 0, CONFIG['ldap']['group_gid'])

        # # change permission
        ## have to think about the
        # for dirs, folds, files in os.walk(subtask_path):
        #     for f in files:
        #         path = os.path.join(dirs, f)
        #         os.chown(path, 0, subtask.assignee.userprofile.location_id + subtask.assignee__userprofile__uid)

        return subtask_path

    if model_type == 'project':
        create_project_folder(model_id)
    elif model_type == 'shot':
        create_shot_folder(model_id)
    elif model_type == 'task':
        create_task_folder(model_id)
    elif model_type == 'subtask':
        create_subtask_folder(model_id)

    return True


@app.task
def create_proxy(first_frame, in_path, out_path):
    """
    ffmpeg -start_number 1000 -i $input_file -c:v libx264 -pix_fmt yuv420p -profile:v high -level 4.2 -crf 1 -preset veryslow -tune film -vf scale=720:-2 -an -movflags +faststart /opt/repos/media/output.mp4
    :return:
    """

    process = subprocess.Popen(
        ['/usr/bin/ffmpeg', '-start_number', str(first_frame), '-i', in_path, '-c:v', 'libx264', '-pix_fmt',
         'yuv420p', '-profile:v', 'high', '-level', '4.2', '-crf', '1', '-preset', 'veryslow', '-tune', 'film',
         '-vf', 'scale=720:-2', '-an', '-movflags', '+faststart', out_path], stderr=subprocess.PIPE,
        stdout=subprocess.PIPE)

    output, error = process.communicate()
    print(error)

    return True


def update_msi_task(record_code, key, value):
    if record_code:
        key_pairs = {'assignee': 'lead_assigned', 'bids': 'bid', 'end_date': 'eta',
                     'status': 'status', 'priority': 'priority', 'complexity': 'complexity'}
        key_name = key_pairs.get(key, None)

        if key_name:
            query = f"update task set {key_name}='{value}' where task.record_code='{record_code}';"

            pnq_conn = psycopg2.connect(host="pnq-db01.digikore.work", dbname="sthpw", user="postgres", password="")
            pnq_curr = pnq_conn.cursor()
            pnq_curr.execute(query)
            pnq_conn.commit()
            pnq_conn.close()

            lax_conn = psycopg2.connect(host="lax-db01.digikore.work", dbname="sthpw", user="postgres", password="")
            lax_curr = lax_conn.cursor()
            lax_curr.execute(query)
            lax_conn.commit()
            lax_conn.close()

    return True


@app.task
def update_msi_note(project_code, login, process, note):
    query = f"""insert into note(project_code, login, process, context, note, record_site)
    values ('{project_code}', '{login}', '{process}', '{process}', '{note}', 'PNQ')"""

    pnq_conn = psycopg2.connect(host="pnq-db01.digikore.work", dbname="sthpw", user="postgres", password="")
    pnq_curr = pnq_conn.cursor()
    pnq_curr.execute(query)
    pnq_conn.commit()
    pnq_conn.close()

    lax_conn = psycopg2.connect(host="lax-db01.digikore.work", dbname="sthpw", user="postgres", password="")
    lax_curr = lax_conn.cursor()
    lax_curr.execute(query)
    lax_conn.commit()
    lax_conn.close()

    return True


@app.task
def update_msi_project(code, key, value):
    query = f"update project set {key}='{value}' where code='{code}'"

    pnq_conn = psycopg2.connect(host="pnq-db01.digikore.work", dbname="sthpw", user="postgres", password="")
    pnq_curr = pnq_conn.cursor()
    pnq_curr.execute(query)
    pnq_conn.commit()
    pnq_conn.close()

    lax_conn = psycopg2.connect(host="lax-db01.digikore.work", dbname="sthpw", user="postgres", password="")
    lax_curr = lax_conn.cursor()
    lax_curr.execute(query)
    lax_conn.commit()
    lax_conn.close()

    return True


@app.task
def update_msi_permissions(project_name):
    # update MSI Permissions in LA

    conn = psycopg2.connect(host="lax-db01.digikore.work", dbname="sthpw", user="postgres", password="")
    cursor = conn.cursor()

    query = f"delete from permission where tool_name='Project' and tag='{project_name}'"
    cursor.execute(query)
    conn.commit()

    query = """select login from login where s_status is null and site in ('LA', 'TC') and category != 'V'"""
    cursor.execute(query)
    users = cursor.fetchall()

    query = "insert into permission (tag, tool_name, username) values {}""".format(
        ', '.join(["('%s', 'Project', '%s')" % (project_name, x[0]) for x in users]))
    cursor.execute(query)
    conn.commit()

    conn.close()

    return True


@app.task
def sync_msi_task(project, sequence, shot, task, task_type):
    task_statuses = {
        'na': 'Not Applicable',
        'Not Required': 'Not Applicable',
        'in_progress': 'In Progress',
        'Completed': 'Final',
        'QC Fail': 'TQC Kickback',
    }

    conn = psycopg2.connect(host="pnq-db01.digikore.work", dbname="sthpw", user="postgres", password="")
    cursor = conn.cursor()

    query = f"""SELECT task.status, task.record_code from task, shot 
        WHERE task.project_code='{project}'
        AND task.context='{task}'
        AND task.process='{task_type}'
        AND shot.sequence_code='{sequence}'
        AND shot.code='{shot}'
        AND shot.record_code=task.parent_record_code"""

    cursor.execute(query)

    for line in cursor.fetchall():
        try:
            task_status, record_code = line
            status = task_statuses[task_status] if task_status in task_statuses else task_status

            task = Task.objects.get(msi_record_code=record_code)
            task.status = TaskStatus.objects.get(name=status)
            task.save()

        except Exception as error:
            print(error)

    return True


@app.task
def sync_msi_subtask(project, sequence, shot, task, subtask, task_type):
    conn = psycopg2.connect(host="pnq-db01.digikore.work", dbname="sthpw", user="postgres", password="")
    cursor = conn.cursor()

    query = f"""SELECT task.status, task.record_code from task, shot 
        WHERE task.project_code='{project}'
        AND task.context='{task}'
        AND task.process='{task_type}'
        AND task.sub_task='{subtask}'
        AND shot.sequence_code='{sequence}'
        AND shot.code='{shot}'
        AND shot.record_code=task.parent_record_code"""

    cursor.execute(query)

    for line in cursor.fetchall():
        try:
            assignee, record_code = line
            subtask = Subtask.objects.get(msi_record_code=record_code)
            subtask.assignee = User.objects.get(username=assignee)
            subtask.save()

        except Exception as error:
            print(error)

    return True


@app.task
def error_log(url, host, error):
    data = {
        "url": url,
        "host": host,
        "error": error,
        "datetime": datetime.datetime.utcnow().isoformat()
    }

    proc = subprocess.Popen(['/usr/bin/curl', '-XPOST', f'http://localhost:9200/error_log/_doc', '-H',
                             'Content-Type: application/json', "-d", json.dumps(data).encode('utf8')],
                            stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    proc.communicate()

    return True


@app.task
def logger(table, data):
    proc = subprocess.Popen(['/usr/bin/curl', '-XPOST', f'http://localhost:9200/{table}/_doc', '-H',
                             'Content-Type: application/json', "-d", json.dumps(data).encode('utf8')],
                            stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    proc.communicate()

    return True


@app.task
def file_transfer(transfer_id):
    transfer = FileTransfer.objects.get(id=transfer_id)
    from_path = transfer.from_path
    to_path = transfer.to_path
    file_count = transfer.files

    transfer.status = 'running'
    transfer.modified_on = datetime.datetime.now()
    transfer.save()

    try:
        if os.path.isdir(from_path):
            new_from_path, _ = os.path.split(from_path)

            counter = 0
            for dirs, folds, files in os.walk(from_path):
                for f in files:
                    src = os.path.join(dirs, f)
                    dst = src.replace(new_from_path, to_path)
                    dst_dir, _ = os.path.split(dst)

                    if not os.path.exists(dst_dir):
                        os.makedirs(dst_dir)

                    # skip if already exists
                    if not os.path.exists(dst):
                        shutil.copy(src, dst, follow_symlinks=True)

                    counter += 1

                FileTransfer.objects.filter(id=transfer_id).update(
                    percent=int((counter / file_count) * 100), modified_on=datetime.datetime.now()
                )

                assert FileTransfer.objects.filter(id=transfer_id).first().cancel is False, 'File transfer canceled.'

            FileTransfer.objects.filter(id=transfer_id).update(status='completed', modified_on=datetime.datetime.now())

        elif os.path.isfile(from_path):
            shutil.copy(from_path, to_path)
            FileTransfer.objects.filter(id=transfer_id).update(percent=100, status='completed',
                                                               modified_on=datetime.datetime.now())

        else:
            raise Exception("Unknown file type.")

    except AssertionError as error:
        FileTransfer.objects.filter(id=transfer_id).update(percent=0, modified_on=datetime.datetime.now())

    except Exception as error:
        message = f"""<p style='white-space: pre-line'>{traceback.format_exc()}</p>"""
        sendmail.delay(f'FILE TRANSFER FAIL', message, ['development@digikore3d.com'],
                       ['io_tech@digikore3d.com', 'pnq_io@digikore.work'])

        FileTransfer.objects.filter(id=transfer_id).update(status='failed', modified_on=datetime.datetime.now())

    return True


@app.task
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

        # update status
        project = Project.objects.get(name=project_name)
        project.status = ProjectStatus.objects.get(name='Archived')
        project.archive_size = archive_size
        project.archive_completed_on = datetime.datetime.now()
        project.save()

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

    except:
        Project.objects.filter(name=project_name).update(status=ProjectStatus.objects.get(name='Ready for Archival'))

        message = f"""<p style='white-space: pre-line'>{traceback.format_exc()}</p>"""

        sendmail.delay(f'PROJECT ARCHIVAL FAILED: {project_name}', message, ['development@digikore3d.com'],
                       ['io_tech@digikore3d.com', 'pnq_io@digikore.work'])


@app.task
def create_gmail_group(group_id):
    group = GmailGroup.objects.get(id=group_id)

    api_credentials = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_JSON_FILE_PATH, scopes='https://www.googleapis.com/auth/admin.directory.group')

    credentials = api_credentials.create_delegated('agarg@digikore3d.com')
    request = build('admin', 'directory_v1', credentials=credentials)
    response = request.groups().insert(body={'email': group.email, 'name': group.name}).execute()
    group.api_id = response['id']
    group.save()

    update_gmail_group_members.delay(group_id)

    return True


@app.task
def update_gmail_group_members(group_id):
    api_credentials = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_JSON_FILE_PATH, scopes='https://www.googleapis.com/auth/admin.directory.group.member')

    credentials = api_credentials.create_delegated('agarg@digikore3d.com')
    request = build('admin', 'directory_v1', credentials=credentials)

    group = GmailGroup.objects.get(id=group_id)
    group_members = list(group.members.all().values_list('email', flat=True))

    # Get existing members from gmail
    gmail_members_resp = request.members().list(groupKey=group.email).execute()
    gmail_members = [x['email'] for x in gmail_members_resp['members']]

    for member in group_members:
        if member not in gmail_members:
            request.members().insert(groupKey=group.email, body={'email': member}).execute()

    for member in gmail_members:
        if member not in group_members:
            request.members().delete(groupKey=group.email, memberKey=member).execute()

    return True
