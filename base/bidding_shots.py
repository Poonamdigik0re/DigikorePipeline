import csv
import datetime
import json
import traceback

from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from base.models import BidShot, Bid, BidStatus, NoteType, Note, TaskType, BidRate
from utils.celery import sendmail, error_log


def parse_datetime(text):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%b %d, %Y", '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except:
            pass

    return None


@permission_required('base.bidding_system')
def home(request, bid_id):
    bid = Bid.objects.get(id=bid_id)
    client = bid.client.name
    project = bid.project

    return render(request, 'bidding_shots.html', {'client': client, 'project': project})


@permission_required('base.bidding_system')
def get_defaults(request, bid_id):
    try:
        bid = Bid.objects.get(id=bid_id)

        resp = {
            'task_types': list(bid.default_tasks.values_list('name', flat=True))
        }

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.bidding_system')
def get_bidshots(request, bid_id):
    try:
        headers = ['id', 'awarded', 'sequence', 'shot', 'task', 'task_type__name', 'bids', 'client_eta', 'internal_eta',
                   'first_frame', 'last_frame', 'plate_version', 'description', 'sup_note']

        data = list(BidShot.objects.filter(bid_id=bid_id).values_list(*headers))

        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.bidding_system')
def save_bidshots(request, bid_id):
    try:
        data = json.loads(request.body)

        bid = Bid.objects.get(id=bid_id)
        assert bid.status.locked is False, "This bid is locked, you can't make any changes."

        for line in data['data']:
            shot_id, awarded, sequence, shot, task, task_type__name, bids, client_eta, internal_eta, first_frame, last_frame, plate_version, description, sup_note = line
            bid_shot = None

            if shot_id:
                bid_shot = BidShot.objects.get(id=shot_id, bid_id=bid_id)

            elif shot and task and task_type__name:
                task_type = TaskType.objects.get(name=task_type__name)
                bid_shot = BidShot(bid_id=bid_id, task_type=task_type, created_by=request.user,
                                   modified_by=request.user)
                bid_shot.save()

            if bid_shot:
                bid_shot.awarded = awarded
                bid_shot.sequence = sequence
                bid_shot.shot = shot
                bid_shot.task = task
                bid_shot.bids = float(bids) if bids else 0
                bid_shot.internal_eta = parse_datetime(internal_eta)
                bid_shot.client_eta = parse_datetime(client_eta)
                bid_shot.first_frame = int(first_frame) if first_frame else 0
                bid_shot.last_frame = int(last_frame) if last_frame else 0
                bid_shot.plate_version = plate_version
                bid_shot.description = description
                bid_shot.sup_note = sup_note
                bid_shot.modified_by = request.user
                bid_shot.save()

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.bidding_system')
def download_bidshots(request, bid_id):
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Project_Import_Template.csv"'

        writer = csv.writer(response)

        headers = ['Awarded', 'Sequence', 'Shot', 'Task', 'Task Type', 'Bids', 'Client ETA', 'Internal ETA',
                   'First Frame', 'Last Frame', 'Plate Ver', 'Task Description', 'Supervisor Note']

        values = ['awarded', 'task_type_id', 'sequence', 'shot', 'task', 'task_type__name', 'bids', 'client_eta',
                  'internal_eta', 'first_frame', 'last_frame', 'plate_version', 'description', 'sup_note']

        if request.user.has_perm('base.bidding_system_bid_rate'):
            headers.append('Rate')

        writer.writerow(headers)

        for bid_shot in list(BidShot.objects.filter(bid_id=bid_id).values_list(*values)):
            bid_shot = list(bid_shot)
            task_type_id = bid_shot.pop(1)

            if request.user.has_perm('base.bidding_system_bid_rate'):
                bid_rate = BidRate.objects.get(bid_id=bid_id, task_type_id=task_type_id).rate
                bid_shot.append(bid_shot[4] * bid_rate)

            writer.writerow(bid_shot)

        return response

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.bidding_system')
def get_bid_status(request, bid_id):
    try:
        return JsonResponse({'status': Bid.objects.get(id=bid_id).status.name})

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.bidding_system')
def update_bid_status(request, bid_id):
    try:
        data = json.loads(request.body)

        assert data['name'] in ['Bidding In Progress', 'Bidding Complete'], "Permission denied"

        status_name = data['name']

        bid = Bid.objects.get(id=bid_id)
        bid.status = BidStatus.objects.get(name=status_name)
        bid.save()

        # Add Note
        note_type_id = NoteType.objects.get(name='Note').id
        Note(parent_id=bid_id, parent_type='bid', text=f'Updated status to {status_name}',
             type_id=note_type_id, created_by=request.user).save()

        # Send Email
        sendmail.delay(f'BID UPDATE: {bid.client.name} / {bid.project}',
                       f'<p>Hi Team,</p><p>{bid.created_by.userprofile.full_name} updated bid status to {status_name}.</p>',
                       ['omkar.shinde@digikore.com'], [])

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
