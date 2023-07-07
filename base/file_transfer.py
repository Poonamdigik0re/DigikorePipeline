import datetime
import json
import os
import re
import traceback

from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from DigikorePortal.settings import MODELS
from base.models import FileTransfer
from utils.celery import file_transfer, error_log


@permission_required('base.file_transfer')
def home(request):
    return render(request, 'file_transfer.html')


@permission_required('base.file_transfer')
def get_active_transfers(request):
    try:
        last_month = datetime.date.today() - datetime.timedelta(days=15)
        resp = list(FileTransfer.objects.filter(created_on__gte=last_month).values(
            *MODELS['default']['file_transfer']).order_by('-id'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.file_transfer')
def browse(request):
    try:
        data = json.loads(request.body)
        path = data['path']
        print(path)
        resp = {'path': path, 'files': []}

        assert re.match('/Users/omkarshinde/Documents/storage/test|/Users/omkarshinde/Documents/storage/test2', path), "Permission denied"

        directories = []
        files = []

        for f in os.scandir(path):
            stats = f.stat()
            data = {
                'name': f.name,
                'path': f.path,
                'size': stats[6],
                'is_dir': f.is_dir()
            }

            if data['is_dir']:
                directories.append(data)
            else:
                files.append(data)

        resp['files'].extend(sorted(directories, key=lambda i: str(i['name']).lower()))
        resp['files'].extend(sorted(files, key=lambda i: str(i['name']).lower()))

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.file_transfer')
def add_folder(request):
    try:
        data = json.loads(request.body)
        path = data['path']

        assert re.match('/Users/omkarshinde/Documents/storage/test|/Users/omkarshinde/Documents/storage/test2', path), "Permission denied"

        os.makedirs(path, 0o770)
        os.chown(path, 0, 80002)

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.file_transfer')
def start_transfer(request):
    try:
        data = json.loads(request.body)
        from_path = data['from_path']
        to_path = data['to_path']

        assert re.match('/Users/omkarshinde/Documents/storage/test|/Users/omkarshinde/Documents/storage/test2', from_path), "Permission denied"
        assert re.match('/Users/omkarshinde/Documents/storage/test|/Users/omkarshinde/Documents/storage/test2', to_path), "Permission denied"

        assert os.path.isdir(to_path), "'To Path' can not be a file, please select a folder"

        resp = {
            'size': 0,
            'files': 0
        }

        if os.path.isfile(from_path):
            print("#")
            resp['size'] = os.path.getsize(from_path)
            resp['files'] = 1

        elif os.path.isdir(from_path):
            for dirs, folds, files in os.walk(from_path):
                for f in files:
                    file_path = os.path.join(dirs, f)
                    resp['files'] += 1
                    resp['size'] += os.path.getsize(file_path)
        else:
            raise Exception('Please select a valid file or folder')

        # Stop scan after 1TB
        # assert resp['size'] < 2199023255552, 'Total size is more that the restricted 2TB limit'
        assert resp['size'] < 104857600, 'Please use Signiant for file size more than 100 MB'
        assert resp['files'] > 0, 'There are no files to transfer in the selected folder'

        transfer = FileTransfer(from_path=from_path, to_path=to_path, size=resp['size'],
                                files=resp['files'], created_by=request.user, status='queued')
        transfer.save()

        file_transfer.delay(transfer.id)

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.file_transfer')
def cancel_transfer(request):
    try:
        data = json.loads(request.body)

        transfer = FileTransfer.objects.get(id=data['transfer_id'])
        transfer.cancel = True
        transfer.status = 'canceled'
        transfer.canceled_by = request.user
        transfer.modified_on = datetime.datetime.now()
        transfer.save()

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.file_transfer')
def restart_transfer(request):
    try:
        data = json.loads(request.body)

        transfer = FileTransfer.objects.get(id=data['transfer_id'])
        transfer.status = 'queued'
        transfer.percent = 0
        transfer.modified_on = datetime.datetime.now()
        transfer.save()

        file_transfer.delay(data['transfer_id'])

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
