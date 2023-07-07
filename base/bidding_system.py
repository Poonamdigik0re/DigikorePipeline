import csv
import json
import traceback

from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from DigikorePortal.settings import MODELS
from base.models import Client, Project, BidStatus, Bid, Note, NoteType, BidRate, TaskType, EmailGroup, BaseRate, \
    BidShot, ProjectType, BaseROP
from utils.celery import sendmail, error_log


@permission_required('base.bidding_system')
def home(request):
    return render(request, 'bidding_system.html')


@permission_required('base.bidding_system')
def get_defaults(request):
    try:
        resp = {
            'all_clients': list(Client.objects.values('id', 'name')),
            'all_projects': list(Project.objects.values('id', 'name')),
            'bid_status': list(BidStatus.objects.values('id', 'name', 'default', 'bg_color', 'fg_color')),
            'task_types': list(TaskType.objects.filter(
                name__in=['roto', 'paint', 'comp', 'depth', 'matchmove']).values('id', 'name')),
            'project_types': list(ProjectType.objects.values('id', 'name'))
        }

        return JsonResponse(resp)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.bidding_system')
def get_client_projects(request):
    try:
        data = json.loads(request.body)
        projects = list(Project.objects.filter(client_id=data['client_id']).values('id', 'name'))

        return JsonResponse(projects, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.bidding_system')
def get_all_bids(request):
    try:
        bids = list(Bid.objects.values(*MODELS['default']['bid']).order_by('-created_on'))

        default_tasks = list(Bid.objects.values('id', 'default_tasks__id'))

        for bid in bids:
            bid['default_tasks'] = [x['default_tasks__id'] for x in default_tasks
                                    if x['id'] == bid['id'] and x['default_tasks__id'] is not None]

        return JsonResponse(bids, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


def send_bidding_request(user, bid):
    bid_rates = ""
    total_bids = 0
    total_cost = 0
    margins = []

    for task_type in bid.default_tasks.all():
        bid_rate, is_new = BidRate.objects.get_or_create(bid=bid, task_type=task_type)
        task_type_name = task_type.name

        if bid.project_type.name == 'VFX':
            if task_type_name in ['roto', 'paint', 'comp']:
                task_type_name = f'vfx_{task_type_name}'

            bids = BidShot.objects.filter(bid=bid, task_type=task_type).aggregate(Sum('bids'))['bids__sum']

            if not bids:
                bids = 0
        else:
            # calculate bids based on rop and frames
            base_budget = 80
            base_rop = BaseROP.objects.get(task_type=task_type.name).rate
            frames = 1440 * (bid.fps / 24)

            bids = round(
                ((frames * bid.stereo_minutes) / base_rop) * (bid.stereo_budget / base_budget) * bid.resolution, 2)

        # todo: enable this later
        # if not bid.status.locked:
        try:
            base_rate = BaseRate.objects.get(task_type=task_type_name)
            bid_rate.base_rate = base_rate.rate
            if is_new or bid_rate.rate == 0:
                bid_rate.rate = base_rate.rate
                bid_rate.save()
        except:
            bid_rate.base_rate = 0
            bid_rate.rate = 0
            bid_rate.save()

        cost = '{:20,.2f}'.format(bid_rate.rate * bids)
        margin = round(((bid_rate.rate - bid_rate.base_rate) / bid_rate.rate) * 100, 2)
        margins.append([margin, bids])

        bid_rates += f"""<tr style="text-align: right">
        <td style="text-align: left">{bid_rate.task_type.name}</td>
        <td>{bids}</td>        
        <td>{cost}</td>
        <td>{margin}%</td>
        </tr>"""

        total_bids += bids
        total_cost += bid_rate.rate * bids

    total_cost = '{:20,.2f}'.format(total_cost)
    weighted_margin = 0

    for _margin, _bids in margins:
        weighted_margin += _margin * _bids / total_bids

    message = f"""<p style='white-space: pre-line'>
    {user.userprofile.full_name} has requested the following bid for approval.
    </p>
    <br>
    <table style="border-collapse: collapse; border: 1px solid black; font-family: sans-serif; width: 60%" border="1" cellpadding="5">
        <thead style="background-color: #ddd">
            <tr style="text-align: right">
                <th style="text-align: left">Task Type</th>
                <th>Total Bids</th>
                <th>Total Price</th>
                <th>Net Margin</th>
            </tr>
        </thead>
        <tbody>
            {bid_rates}
        </tbody>
        <tfoot style="background-color: #ddd">
            <tr style="text-align: right">
                <th style="text-align: left">Total</th>
                <th>{round(total_bids, 2)}</th>
                <th>{total_cost}</th>
                <th>{round(weighted_margin, 2)}%</th>
            </tr>
        </tfoot>
    </table>"""

    email_group = EmailGroup.objects.get(name='BID_APPROVAL')
    mail_to = email_group.mail_to.split(';')
    cc_to = email_group.cc_to.split(';') if email_group.cc_to else []
    cc_to.append(user.email)

    sendmail.delay(f'BID APPROVAL: {bid.client.name} / {bid.project} / {bid.name}', message, mail_to, cc_to,
                   reply_to='bidding@digikore.com')

    return True


@permission_required('base.bidding_system')
def add_bid(request):
    try:
        data = json.loads(request.body)
        bid_id = data.get('id', None)

        default_tasks = data.get('default_tasks', [])
        data.pop('default_tasks')

        if bid_id:
            bid = Bid.objects.get(id=bid_id)

            assert bid.status.locked is False, "This bid is locked, you can't make any changes."

            for k, v in data.items():
                if hasattr(bid, k) and v:
                    if str(getattr(bid, k)) != v:
                        setattr(bid, k, v)

            bid.modified_by = request.user
            bid.save()

            # email subject
            subject = f"{request.user.userprofile.full_name} has updated the following bid bid"

        else:
            bid = Bid(client_id=data['client_id'],
                      project=data['project'],
                      project_type_id=data['project_type_id'],
                      name=data['name'],

                      stereo_budget=data['stereo_budget'],
                      stereo_minutes=data['stereo_minutes'],
                      resolution=data['resolution'],
                      fps=data['fps'],

                      start_date=data['start_date'],
                      end_date=data['end_date'],
                      status=BidStatus.objects.get(default=True),

                      purchase_order=data['purchase_order'],
                      invoice_number=data['invoice_number'],
                      created_by=request.user,
                      modified_by=request.user)
            bid.save()

            # # Create directory
            # if not CONFIG['default']['debug']:
            #     bid_dir = f'/digi/prod/_uBidding/{bid.client.name}/{bid.project}/{bid.created_on.strftime("%Y%m%d")}'
            #     if not os.path.exists(bid_dir):
            #         os.makedirs(bid_dir, 0o775)

            # email subject
            subject = f"{request.user.userprofile.full_name} has created a new bid"

        if default_tasks:
            bid.default_tasks.set([int(x) for x in default_tasks])
            bid.save()

        if bid.project_type.name == 'Stereo':
            bid.default_tasks.set(TaskType.objects.filter(name__in=('roto', 'paint', 'depth', 'comp')))
            bid.save()

        # Send Email
        message = f"""<p style='white-space: pre-line'>
        Hi Team,

        {subject}
        </p>
        <br>
        <table style="border-collapse: collapse; border: 1px solid black; font-family: sans-serif" border="1" cellpadding="5">
            <tbody>
            <tr>
                <th>Client</th>
                <td>{bid.client.name}</td>
            </tr>
            <tr>
                <th>Project</th>
                <td>{bid.project}</td>
            </tr>
            <tr>
                <th>Type</>
                <td>{bid.project_type}</td>
            </tr>
            <tr>
                <th>Name</th>
                <td>{bid.name}</td>
            </tr>
            <tr>
                <th>Start Date</th>
                <td>{bid.start_date}</td>
            </tr>
            <tr>
                <th>End Date</th>
                <td>{bid.end_date}</td>
            </tr>
            <tr>
                <th>Purchase Order</th>
                <td>{bid.purchase_order}</td>
            </tr>
            <tr>
                <th>Invoice Number</th>
                <td>{bid.invoice_number}</td>
            </tr>
            
            <tr>
                <th>Resolution</>
                <td>{bid.resolution}</td>
            </tr>
            <tr>
                <th>FPS</>
                <td>{bid.fps}</td>
            </tr>
            <tr>
                <th>Stereo Budget</>
                <td>{bid.stereo_budget}</td>
            </tr>
            <tr>
                <th>Stereo Minutes</>
                <td>{bid.stereo_minutes}</td>
            </tr>
            </tbody>
        </table>
        """

        email_group = EmailGroup.objects.get(name='BID_UPDATE')
        mail_to = email_group.mail_to.split(';')
        cc_to = email_group.cc_to.split(';') if email_group.cc_to else []

        sendmail.delay(f'BID UPDATE: {bid.client.name} / {bid.project} / {bid.name}', message, mail_to, cc_to)

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.bidding_system')
def update_bid_status(request):
    try:
        data = json.loads(request.body)
        bid_id = data['id']
        reason = data.get('reason', None)

        bid = Bid.objects.get(id=bid_id)

        if not request.user.is_superuser:
            assert bid.status.locked is False, "This bid is locked, you can't make any changes."

        bid_status = BidStatus.objects.get(id=data['status_id'])
        status_name = bid_status.name

        # Update Bid
        bid.status = bid_status
        bid.rejected_for = reason
        bid.modified_by = request.user
        bid.save()

        # Add Note
        note_type_id = NoteType.objects.get(name='Note').id
        Note(parent_id=bid_id, parent_type='bid', text=f'Updated status to {status_name}',
             type_id=note_type_id, created_by=request.user).save()

        # Send Email for either bidding approval or status change
        if bid.status.name == 'Requested for Approval':
            send_bidding_request(request.user, bid)
        else:
            email_group = EmailGroup.objects.get(name='BID_UPDATE')
            mail_to = email_group.mail_to.split(';')
            cc_to = email_group.cc_to.split(';') if email_group.cc_to else []

            sendmail.delay(f'BID UPDATE: {bid.client.name} / {bid.project} / {bid.name}',
                           f'<p>Hi Team,</p><p>{request.user.userprofile.full_name} updated bid status to <b>{status_name}</b>.</p>',
                           mail_to, cc_to)

        return JsonResponse({'id': bid_status.id,
                             'name': status_name,
                             'bg_color': bid_status.bg_color,
                             'fg_color': bid_status.fg_color})

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.bidding_system_bid_rate')
def get_base_rates(request):
    try:
        resp = list(BaseRate.objects.values('task_type', 'rate'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.bidding_system_bid_rate')
def get_base_rop(request):
    try:
        resp = list(BaseROP.objects.values('task_type', 'rate'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.bidding_system_bid_rate')
def get_bid_rates(request):
    try:
        data = json.loads(request.body)

        bid = Bid.objects.get(id=data['bid_id'])
        bid_rates = []

        for task_type in bid.default_tasks.all():
            bid_rate, is_new = BidRate.objects.get_or_create(bid=bid, task_type=task_type)
            task_type_name = task_type.name

            if bid.project_type.name == 'VFX':
                if task_type_name in ['roto', 'paint', 'comp']:
                    task_type_name = f'vfx_{task_type_name}'

                bids = BidShot.objects.filter(bid=bid, task_type=task_type).aggregate(Sum('bids'))['bids__sum']

            else:
                # calculate bids based on rop and frames
                base_budget = 80
                base_rop = BaseROP.objects.get(task_type=task_type.name).rate
                frames = 1440 * (bid.fps / 24)

                bids = round(
                    ((frames * bid.stereo_minutes) / base_rop) * (bid.stereo_budget / base_budget) * bid.resolution, 0)

            # todo: enable this later
            # if bid.status.locked is False:
            try:
                base_rate = BaseRate.objects.get(task_type=task_type_name)
                bid_rate.base_rate = base_rate.rate
                if is_new or bid_rate.rate == 0:
                    bid_rate.rate = base_rate.rate
                bid_rate.save()
            except:
                bid_rate.base_rate = 0
                bid_rate.rate = 0
                bid_rate.save()

            bid_rates.append({'id': bid_rate.id, 'task_type__name': bid_rate.task_type.name,
                              'base_rate': bid_rate.base_rate, 'rate': bid_rate.rate, 'bids': bids})

        return JsonResponse(bid_rates, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.bidding_system_bid_rate')
def update_bid_rates(request):
    try:
        data = json.loads(request.body)

        bid = Bid.objects.get(id=data['bid_id'])

        assert bid.status.locked is False, "This bid is locked, you can't make any changes."

        for bid_rate in data['bid_rates']:
            BidRate.objects.filter(bid_id=data['bid_id'], id=bid_rate['id']).update(rate=bid_rate['rate'])

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


def download_summary(request):
    try:
        assert request.user.is_superuser, 'Permission denied'

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="Bidding_Report.csv"'

        writer = csv.writer(response)

        writer.writerow(['Status', 'Client', 'Project', 'Task Type', 'Cost'])

        data = {}

        for bid in Bid.objects.all():
            client_name = bid.client.name
            status_name = bid.status.name
            project_name = bid.project
            project_type = bid.project_type.name

            if status_name not in data:
                data[status_name] = {}

            if client_name not in data[status_name]:
                data[status_name][client_name] = {}

            if project_name not in data[status_name][client_name]:
                data[status_name][client_name][project_name] = {}

            bid_default_tasks = bid.default_tasks.all().values_list('id', flat=True)

            for shot_task_type in list(
                    set(BidShot.objects.filter(bid_id=bid.id).values_list('task_type_id', flat=True))):
                if shot_task_type not in bid_default_tasks:
                    bid.default_tasks.add(shot_task_type)

            for task_type in bid.default_tasks.all().values('id', 'name'):

                if project_type == 'VFX' and BidShot.objects.filter(task_type_id=task_type['id'], bid=bid).count() == 0:
                    bid.default_tasks.remove(task_type['id'])
                    continue

                task_type_name = task_type['name']

                if project_type == 'VFX':
                    if task_type_name in ['roto', 'paint', 'comp']:
                        task_type_name = f'vfx_{task_type_name}'

                    bids = BidShot.objects.filter(bid=bid, task_type_id=task_type['id']).aggregate(Sum('bids'))[
                        'bids__sum']

                    if not bids:
                        bids = 0
                else:
                    # calculate bids based on rop and frames
                    base_budget = 80
                    base_rop = BaseROP.objects.get(task_type=task_type['name']).rate
                    frames = 1440 * (bid.fps / 24)

                    bids = round(
                        ((frames * bid.stereo_minutes) / base_rop) * (bid.stereo_budget / base_budget) * bid.resolution,
                        2)

                bid_rate, is_new = BidRate.objects.get_or_create(bid=bid, task_type_id=task_type['id'])

                try:
                    base_rate = BaseRate.objects.get(task_type=task_type_name)
                    bid_rate.base_rate = base_rate.rate
                    if is_new or bid_rate.rate == 0:
                        bid_rate.rate = base_rate.rate
                        bid_rate.save()

                except ObjectDoesNotExist:
                    bid_rate.base_rate = 0
                    bid_rate.rate = 0
                    bid_rate.save()

                if task_type_name not in data[status_name][client_name][project_name]:
                    data[status_name][client_name][project_name][task_type_name] = 0

                data[status_name][client_name][project_name][task_type_name] += bid_rate.rate * bids

        for status, clients in data.items():
            for client, projects in clients.items():
                for project, task_types in projects.items():
                    for task_type, price in task_types.items():
                        writer.writerow([status, client, project, task_type, price])

        return response

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
