import json
import re
import traceback

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render

from DigikorePortal.settings import FOLDERS
from base.models import *
from utils.celery import create_proxy, error_log


@permission_required('base.ingest_system')
def home(request):
    return render(request, 'ingest_system.html')


@permission_required('base.ingest_system')
def get_defaults(request):
    try:
        resp = {
            'file_type': list(FilerecordType.objects.values('id', 'name')),
            'file_status': list(FilerecordStatus.objects.values('id', 'name'))
        }
        print(resp)

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.ingest_system')
def get_projects(request):
    try:
        data = list(Project.objects.values('id', 'name'))
        print("project:",data)

        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.ingest_system')
def get_parents(request):
    try:
        data = json.loads(request.body)
        project_id = data['project_id']
        model_type = data['model_type']

        model_class = globals()[model_type.title()]
        if model_type == 'project':
            resp = list(model_class.objects.filter(id=project_id).values('id', 'name'))
        else:
            resp = list(model_class.objects.filter(project_id=project_id).values('id', 'name'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.ingest_system')
def get_data(request):
    try:
        data = json.loads(request.body)
        print("**:",data)
        sequence_regex = '(.*)(\.|-|_)(\d+)(\.\w+)$'
        unique_files = []
        resp = {}

        for dirs, folds, files in os.walk(data['path']):
            for f in files:
                sequence_match = re.match(sequence_regex, f)
                if sequence_match:
                    name, connector, frame, extension = sequence_match.groups()
                    if name not in unique_files:
                        unique_files.append(name)
                        resp[name] = {'name': name, 'frames': [int(frame)], 'extension': extension, 'client_name': name,
                                      'padding': len(frame), 'path': dirs, 'connector': connector, 'is_sequence': True}
                    else:
                        resp[name]['frames'].append(int(frame))

                else:
                    name, extension = os.path.splitext(f)
                    if name not in unique_files:
                        unique_files.append(name)

                        resp[name] = {'name': name, 'extension': extension, 'path': dirs, 'frames': [0],
                                      'is_sequence': False, 'padding': 0, 'client_name': name}

        data = list(resp.values())

        for d in data:
            d['first_frame'] = min(d['frames'])
            d['last_frame'] = max(d['frames'])
            d.pop('frames')

        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.ingest_system')
def get_version(request):
    try:
        data = json.loads(request.body)
        version = Filerecord.objects.filter(parent_type=data['parent_type'],
                                            parent_id=data['parent_id'],
                                            name=data['name'],
                                            type_id=data['type_id']).count() + 1

        return HttpResponse(version)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.ingest_system')
def start_ingest(request):
    def get_project_path(model_id):
        project = Project.objects.get(id=model_id)

        root_path = FOLDERS['root']['project']
        parent_path = FOLDERS['project']['path'].format(root_project=root_path, name=project.name)

        return parent_path

    def get_shot_path(model_id):
        shot = Shot.objects.get(id=model_id)

        shot_path = FOLDERS['shot']['path'].format(sequence_path=shot.sequence, name=shot.name)

        return shot_path

    try:
        data = json.loads(request.body)
        project_path = get_project_path(data['project_id'])

        for d in data['data']:
            file_type = FilerecordType.objects.get(id=d['type_id']).name

            version = "v{0:03d}".format(int(d['version']))
            model_path = locals()[f'get_{d["parent_type"]}_path'](d['parent_id'])

            source_dir = d['path']
            dest_dir = f'{model_path}/files/{file_type}/{d["name"]}/{version}'

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, 0o755)

            if d['is_sequence']:
                for i in range(d['first_frame'], d['last_frame'] + 1):
                    _frame = str(i).zfill(d['padding'])
                    source_file_name = f'{d["client_name"]}{d["connector"]}{_frame}{d["extension"]}'
                    dest_file_name = f'{d["name"]}_{version}{d["connector"]}{_frame}{d["extension"]}'

                    source_file = f'{source_dir}/{source_file_name}'
                    dest_file = f'{dest_dir}/{dest_file_name}'

                    try:
                        os.link(source_file, dest_file)
                        os.chmod(source_file, 0o755)
                    except FileExistsError:
                        pass

                # update dest file path
                d['path'] = f'{dest_dir}/{d["name"]}_{version}{d["connector"]}%0{d["padding"]}d{d["extension"]}'

                # safe file path
                Filerecord(project_id=data['project_id'], created_by=request.user,
                           status=FilerecordStatus.objects.get(default=True), **d).save()

                source_path = f'{source_dir}/{d["client_name"]}{d["connector"]}%0{d["padding"]}d{d["extension"]}'
                output_path = os.path.join(project_path, 'proxies', f'{d["name"]}_{version}.mp4')
                create_proxy.delay(d['first_frame'], source_path, output_path)

            else:
                source_file_name = f'{d["client_name"]}{d["extension"]}'
                source_file = f'{source_dir}/{source_file_name}'

                dest_file_name = f'{d["name"]}{d["extension"]}'
                dest_file = f'{dest_dir}/{dest_file_name}'

                os.link(source_file, dest_file)
                os.chmod(source_file, 0o755)

                # update dest file path
                d['path'] = f'{dest_dir}/{d["name"]}_{version}d{d["extension"]}'

                # safe file path
                Filerecord(project_id=data['project_id'], created_by=request.user,
                           status=FilerecordStatus.objects.get(default=True), **d).save()

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
