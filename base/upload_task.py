import json
import traceback
import csv
from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.conf import settings

from DigikorePortal.settings import MODELS
from base.models import *
from utils.celery import error_log
from django.db import connection
from datetime import datetime
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from io import StringIO
from django.core.exceptions import ValidationError
import os
from django.core.files.storage import FileSystemStorage
import glob
import ast
from django.views.decorators.csrf import csrf_exempt


@login_required
def home(request):
    return render(request, 'upload_task.html')


def upload_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        savefile = FileSystemStorage()
        name = savefile.save(csv_file.name, csv_file)  # gets the name of the file

        d = os.getcwd()  # how we get the current directory
        file_directory = os.path.join(d, 'media', name)  # saving the file in the media directory

        current_file_name = csv_file.name
        media_path = os.path.join(settings.MEDIA_ROOT, current_file_name)

        with open(media_path, 'r') as file:
            csv_contents = file.read().splitlines()

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
            print(data)
        return render(request, 'upload_task.html', {'data': data})
    else:
        return render(request, 'upload_task.html')




def get_id_from_name(table, field_name, value):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id FROM {table} WHERE {field_name} = %s", [value])
        result = cursor.fetchone()
        if result:
            return result[0]
        return None

def get_userid_from_name(table, field_name, value):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT user_id FROM {table} WHERE {field_name} = %s", [value])
        result = cursor.fetchone()
        if result:
            return result[0]
        return None

def add_uploaded_data(data, request):
    reader = data
    # print("$$$:",reader)
    for i in reader:
        # print(i)
        description = i['Description']
        bids = i['Bids']
        actuals = i['Actuals']
        start_date = i['Start Date']
        end_date = i['End Date']
        working_first_frame = i['Working first frame']
        working_last_frame = i['Working last frame']
        project_id = get_id_from_name("base_project", "name", i['Project'])
        status_id = get_id_from_name("base_taskstatus", "name", i['status'])
        department = get_id_from_name("base_department", "name", i['Department Name'])
        assignee_id = get_userid_from_name("base_userprofile", "full_name", i['Assignee Name'])
        # complexity_id = i['Complexity']
        priority_id = get_id_from_name("base_taskpriority", "name", i['Priority'])
        type_id = get_id_from_name("base_tasktype", "name",i['Type'])
        vendor_id =get_id_from_name("base_vendor", "name", i['vendor'])
        name = i['Name']
        due_date = i['Due date']
        start_frame = i['Start Frame']
        end_frame = i['End Frame']
        turnover_no = i['Turnover No']
        scope_of_work = i['Scope of Work']
        thumbnail = i['Thumbnail']
        shot_id = get_id_from_name("base_shot", "name", i['Shot name'])

        print(project_id)
        print(assignee_id)
        # print(request.user.id)

        task = Task(
            name=name,
            bids=bids,
            actuals=actuals,
            scope_of_work=scope_of_work,
            project_id=project_id,
            description=description,
            start_date=start_date,
            end_date=end_date,
            due_date=due_date,
            working_first_frame=working_first_frame,
            working_last_frame=working_last_frame,
            start_frame=start_frame,
            end_frame=end_frame,
            assignee_id=assignee_id,
            priority_id=priority_id,
            status_id=status_id,
            type_id=type_id,
            vendor_id=vendor_id,
            shot_id=shot_id,
            department_id=department,
            turnover_no=turnover_no,
            thumbnail=thumbnail
        )

        # print(task)
        task.save()




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
        data = request.POST.getlist('data[]')

        # Get the current working directory
        base_directory = os.getcwd()

        # Create the 'edited_csv' directory
        edited_csv_directory = os.path.join(base_directory, 'edited_csv')
        os.makedirs(edited_csv_directory, exist_ok=True)

        # Generate a unique filename for the edited CSV file
        filename = datetime.now().strftime('task-%Y-%m-%d-%H-%M.csv')
        file_path = os.path.join(edited_csv_directory, filename)

        # Specify the column order
        columns = [
            "Description", "Bids", "Actuals", "Start Date", "End Date",
            "Working first frame", "Working last frame", "Assignee Name",
            "Priority", "Project", "status", "Type", "vendor", "Name",
            "Due date", "Start Frame",""
            "End Frame", "Turnover No", "Scope of Work", "Thumbnail", "Shot name", "Department Name"
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
            add_uploaded_data(rows, request)

        return HttpResponse('CSV file updated successfully.')
    else:
        return HttpResponse('Invalid request method.')



