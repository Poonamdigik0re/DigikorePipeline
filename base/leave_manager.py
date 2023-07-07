import datetime
import json
import traceback

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.shortcuts import render

from base.models import Leave, LeaveLog, Compoff
from utils.celery import error_log


@permission_required('base.leave_manager')
def home(request):
    return render(request, 'leave_manager.html')


@permission_required('base.leave_manager')
def get_leave_count(request):
    try:
        profile = request.user.userprofile
        resp = {'paid_leave': profile.paid_leave, 'casual_leave': profile.casual_leave, 'comp_off': profile.comp_off}

        return JsonResponse(resp, safe=True)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.leave_manager')
def get_leave_log(request):
    try:
        resp = list(LeaveLog.objects.filter(user=request.user, created_on__year=datetime.date.today().year).values(
            'created_on', 'total_days', 'leave_type', 'comment').order_by('-created_on'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.leave_manager')
def apply_leave(request):
    try:
        data = json.loads(request.body)
        today = datetime.date.today()

        profile = request.user.userprofile
        leave_type = data['leave_type']
        from_date = datetime.datetime.strptime(data['from_date'], '%Y-%m-%d')
        to_date = datetime.datetime.strptime(data['to_date'], '%Y-%m-%d')
        reason = data['reason'].strip()

        total_days = (to_date - from_date).days + 1

        last_approval_date = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=26)
        if today.day >= 26:
            last_approval_date = today.replace(day=26)

        # Check for confirmation status
        assert profile.confirmation_status in ('pending', 'confirmed'), "You are not allowed to apply for leaves"

        if leave_type != 'comp_off':
            assert profile.confirmation_status == 'confirmed', 'Not allowed to apply leaves in probation period'

        # Check dates
        assert from_date >= last_approval_date, "Can't apply leaves for previous payroll"
        assert to_date >= from_date, '"To date" can not be before "from date"'
        assert to_date.year <= today.year, "You can only apply leaves for current year."

        # Check leave availability
        available_leave = getattr(profile, leave_type, 0)
        assert total_days <= available_leave

        # Check for duplicate request
        assert Leave.objects.filter(user=profile.user, from_date=from_date, status__in=['pending', 'approved'],
                                    to_date=to_date).count() == 0, 'Duplicate leave'

        # Apply for leave
        leave = Leave(user=request.user, from_date=from_date, to_date=to_date, total_days=total_days,
                      created_by=request.user, reason=reason, leave_type=leave_type)
        leave.save()

        # Update UserProfile
        setattr(profile, leave_type, available_leave - total_days)
        profile.save()

        # Save Log
        LeaveLog(user=leave.user, leave_type=leave.leave_type, total_days=leave.total_days * -1,
                 comment='Leaves Applied from %s to %s' % (
                     leave.from_date.strftime('%b %d, %Y'), leave.to_date.strftime('%b %d, %Y')),
                 created_by=request.user).save()

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.leave_manager')
def cancel_leave(request):
    try:
        data = json.loads(request.body)

        leave = Leave.objects.get(id=data['id'])
        profile = leave.user.userprofile

        last_approval_date = (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).replace(day=26)
        if datetime.date.today().day >= 26:
            last_approval_date = datetime.date.today().replace(day=26)

        # Check leave status and user
        assert leave.user == request.user, 'You do not have permission to cancel this leave'
        assert leave.status == 'pending' or \
               (leave.status == 'approved' and leave.from_date >= last_approval_date), 'Can not cancel this leave.'

        leave.updated_by = request.user
        leave.updated_on = datetime.datetime.now()
        leave.status = 'canceled'
        leave.save()

        # Reimburse the leaves
        curr_leaves = getattr(profile, leave.leave_type, 0)
        new_leaves = curr_leaves + leave.total_days
        setattr(profile, leave.leave_type, new_leaves)
        profile.save()

        # Save into log
        LeaveLog(user=leave.user, leave_type=leave.leave_type, total_days=leave.total_days,
                 comment='Leaves Canceled for %s-%s' % (leave.from_date.strftime('%b %d, %Y'),
                                                        leave.to_date.strftime('%b %d, %Y')),
                 created_by=request.user).save()

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.leave_manager')
def reject_leave(request):
    try:
        data = json.loads(request.body)
        resp = []

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.leave_manager')
def approve_leave(request):
    try:
        data = json.loads(request.body)
        resp = []

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.leave_manager')
def get_all_leaves(request):
    try:
        values = ('id', 'user_id', 'user__userprofile__full_name',
                  'user__userprofile__team__lead__userprofile__full_name',
                  'from_date', 'to_date', 'total_days', 'status', 'leave_type', 'created_on', 'reason', 'rejection')

        resp = list(Leave.objects.filter(user=request.user, from_date__year=datetime.date.today().year).values(
            *values).order_by('-created_on'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.leave_manager')
def get_all_comp_offs(request):
    try:
        values = ('id', 'user_id', 'user__userprofile__full_name',
                  'user__userprofile__team__lead__userprofile__full_name',
                  'date', 'total_days', 'status', 'reason', 'rejection', 'can_be_incentive')

        resp = list(Compoff.objects.filter(user=request.user, date__year=datetime.date.today().year).values(
            *values).order_by('-created_on'))

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.leave_manager')
def get_all_late_marks(request):
    try:
        resp = []

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
