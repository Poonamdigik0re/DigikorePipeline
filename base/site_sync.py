import traceback

import psycopg2
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.http.response import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render

from utils.celery import error_log


def connect_msi_pnq():
    conn = psycopg2.connect(host="pnq-db01.digikore.work", dbname="sthpw", user="postgres", password="")

    return conn


def connect_msi_lax():
    conn = psycopg2.connect(host="tcdb01.lfilms.net", dbname="sthpw", user="postgres", password="")

    return conn


@permission_required('base.site_sync')
def home(request):
    return render(request, 'site_sync.html')


@permission_required('base.site_sync')
def get_status_breakdown(request, location):
    try:
        if location == 'pnq':
            conn = connect_msi_pnq()
        else:
            conn = connect_msi_lax()

        cursor = conn.cursor()
        query = "select count(*), status, sum(st_size) from site_sync where status not in ('complete', 'deleted', 'sig_finished', 'remote_sync') GROUP BY status;"
        cursor.execute(query)
        data = []

        for line in cursor.fetchall():
            count, status, size = line
            data.append({'count': count, 'status': status, 'size': size})

        # close connection
        conn.close()

        return JsonResponse(data, safe=False)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@permission_required('base.site_sync')
def get_project_breakdown(request, location):
    try:
        if location == 'pnq':
            conn = connect_msi_pnq()
        else:
            conn = connect_msi_lax()

        cursor = conn.cursor()
        query = "select count(*), SPLIT_PART(relative_dir, '/', 1), sum(st_size) from site_sync where status in ('sig_ready', 'sig_submitted') GROUP BY SPLIT_PART(relative_dir, '/', 1);"
        cursor.execute(query)
        data = []

        for line in cursor.fetchall():
            count, project, size = line
            if project:
                data.append({'count': count, 'project': project, 'size': size})

        # close connection
        conn.close()

        return JsonResponse(data, safe=False)

    except Exception as error:
        return HttpResponseBadRequest(error)


@permission_required('base.site_sync')
def fix_sig_submitted(request):
    try:
        conn = connect_msi_pnq()
        cursor = conn.cursor()
        query = "update site_sync set status='sig_ready' where status='sig_submitted'"
        cursor.execute(query)
        conn.commit()
        conn.close()

        conn = connect_msi_lax()
        cursor = conn.cursor()
        query = "update site_sync set status='sig_ready' where status='sig_submitted'"
        cursor.execute(query)
        conn.commit()
        conn.close()

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
