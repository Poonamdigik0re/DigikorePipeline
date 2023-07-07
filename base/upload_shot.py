import json
import traceback
from django.conf import settings
from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from DigikorePortal.settings import MODELS
from base.models import UserProfile, Project, Shot, Task, Subtask, BidActual, Workstation, Attendance
from base.models import *
from utils.celery import error_log
import csv
import os
import glob
from datetime import datetime
from io import StringIO
from csv import DictReader
from django.db import connection
from django.views.decorators.csrf import csrf_exempt




@login_required
def home(request):
    return render(request, 'upload_shot.html')


def upload_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        print(csv_file)
        savefile = FileSystemStorage()
        name = savefile.save(csv_file.name, csv_file)  # gets the name of the file

        d = os.getcwd()  # how we get the current directory
        file_directory = os.path.join(d, 'media', name)  # saving the file in the media directory

        current_file_name = csv_file.name
        media_path = os.path.join(settings.MEDIA_ROOT, current_file_name)
    #
        with open(media_path, 'r') as file:
            csv_contents = file.read().splitlines()
    #
        reader = csv.reader(csv_contents)
        data = list(reader)
        rows = []  # List to store all rows

        if len(data) > 0:
            header = data[0]

            for row in data[1:]:
                row_data = {}  # Dictionary to store each row's data
                for header_value, value in zip(header, row):
                    row_data[header_value] = value
                rows.append(row_data)
        print(rows)
        return render(request, 'upload_shot.html', {'data': data})
    else:
        return render(request, 'upload_shot.html')

def get_id_from_name(table, field_name, value):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id FROM {table} WHERE {field_name} = %s", [value])
        result = cursor.fetchone()
        if result:
            return result[0]
        return None

def get_shot_id_from_name(table, field_name, value):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id FROM {table} WHERE {field_name} = %s", [value])
        result = cursor.fetchone()
        if result:
            return result[0]
        return None


def add_uploaded_data(data, request):
    reader = data
    # print("$$$:",reader)
    for i in reader:
        # print(i)
        shot_name = i['Shot Name']
        start_date = i['start_date']
        end_date = i['end_date']
        client_first_frame = i['client_first_frame']
        client_last_frame = i['client_last_frame']
        working_first_frame = i['working_first_frame']
        working_last_frame = i['working_last_frame']
        project_name = get_id_from_name("base_project", "name", i['project_name'])
        status = get_id_from_name("base_shotstatus", "name", i['status'])
        department = get_id_from_name("base_department", "name", i['department'])
        reel = i['reel']
        scene = i['scene']
        sequence = i['sequence']
        episode = i['episode']
        annotation = i['annotation']
        bids = i['bids']
        client_feedback = i['client_feedback']
        client_remarks = i['client_remarks']
        description = i['description']
        execution_type = i['execution_type']
        fps = i['fps']
        internal_approval_id = i['internal_approval_id'] if i['internal_approval_id'] else None
        internal_supervisor_remarks = i['internal_supervisor_remarks']
        resolution = i['resolution']
        show_name = i['show_name']
        thumbnail = i['thumbnail']
        vault_url = i['vault_url']

        print(fps)

        # print(request.user.id)

        shot = Shot(
            name = shot_name,
            start_date = start_date,
            end_date = end_date,
            client_first_frame = client_first_frame,
            client_last_frame = client_last_frame,
            working_first_frame = working_first_frame,
            working_last_frame = working_last_frame,
            project_id = project_name,
            status_id = status,
            reel = reel,
            created_by_id = request.user.id,
            created_on =datetime.now(),
            scene = scene,
            sequence = sequence,
            episode = episode,
            annotation = annotation,
            bids = bids,
            fps = fps,
            client_feedback = client_feedback,
            client_remarks = client_remarks,
            description = description,
            execution_type = execution_type,
            internal_approval_id = internal_approval_id,
            internal_supervisor_remarks = internal_supervisor_remarks,
            resolution = resolution,
            show_name = show_name,
            thumbnail = thumbnail,
            vault_url = vault_url
        )



        #
        shot.save()

        shot_id = get_shot_id_from_name("base_shot", "name", i['Shot Name'])
        print(shot_id)


        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO base_shot_department(shot_id, department_id) values (%s, %s)",[shot_id,department])
            connection.commit()
        return HttpResponse('Shot added successfully')


    return render(request, 'upload_shot.html')

def submit_csv(request):
    print('****')
    media_directory = settings.MEDIA_ROOT
    csv_files = glob.glob(os.path.join(media_directory, '*.csv'))
    csv_files.sort(key=os.path.getmtime, reverse=True)
    if csv_files:
        latest_csv_file = csv_files[0]

        # with open(latest_csv_file, 'r', encoding='utf-8') as file:
        #     csv_contents = file.read().splitlines()
        #     csv_string = StringIO('\n'.join(csv_contents))
        #     reader = csv.reader(csv_string)
        #     next(reader)

        with open(latest_csv_file, 'r') as file:
            csv_contents = file.read().splitlines()
        #
        reader = csv.reader(csv_contents)
        data = list(reader)
        rows = []  # List to store all rows

        if len(data) > 0:
            header = data[0]

            for row in data[1:]:
                row_data = {}  # Dictionary to store each row's data
                for header_value, value in zip(header, row):
                    row_data[header_value] = value
                rows.append(row_data)

        # Call the function and pass the reader variable as an argument
        add_uploaded_data(rows, request)

    return render(request, 'upload_shot.html')

@csrf_exempt
def update_csv(request):
    if request.method == 'POST':
        print("####")
        data = request.POST.getlist('data[]')

        # Get the current working directory
        base_directory = os.getcwd()

        # Create the 'edited_csv' directory
        edited_csv_directory = os.path.join(base_directory, 'edited_csv')
        os.makedirs(edited_csv_directory, exist_ok=True)

        # Generate a unique filename for the edited CSV file
        filename = datetime.now().strftime('shot-%Y-%m-%d-%H-%M.csv')
        file_path = os.path.join(edited_csv_directory, filename)

        # Specify the column order
        columns = [
            "id","Shot Name", "start_date", "end_date", "client_first_frame", "client_last_frame", "working_first_frame",
            "working_last_frame", "project_name", "status", "reel", "scene", "sequence",
            "episode", "annotation","bids",
            "client_feedback", "client_remarks", "description", "execution_type", "fps",
            "internal_approval_id", "internal_supervisor_remarks", "resolution",
            "show_name", "thumbnail", "vault_url","department",
        ]

        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(columns)

            for row in data:
                values = row.split(',')

                # Write values to the CSV file
                writer.writerow(values)

        # Get the latest edited CSV file in the 'edited_csv' directory
        csv_files = glob.glob(os.path.join(edited_csv_directory, '*.csv'))
        csv_files.sort(key=os.path.getmtime, reverse=True)
        if csv_files:
            latest_csv_file = csv_files[0]

            with open(latest_csv_file, 'r') as file:
                csv_contents = file.read().splitlines()
            #
            reader = csv.reader(csv_contents)
            data = list(reader)
            rows = []  # List to store all rows

            if len(data) > 0:
                header = data[0]

                for row in data[1:]:
                    row_data = {}  # Dictionary to store each row's data
                    for header_value, value in zip(header, row):
                        row_data[header_value] = value
                    rows.append(row_data)

            # Call the function and pass the reader variable as an argument
            print(rows)
            add_uploaded_data(rows, request)



        return render(request, 'upload_shot.html')
    else:
        return HttpResponse('Invalid request method.')
