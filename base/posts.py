import datetime
import json
import traceback

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from base.models import Post, Vote
from utils.celery import error_log


@login_required
def home(request):
    return render(request, 'posts.html')


@login_required
def get_all_posts(request):
    """
    :param request:
    :return: [{'id': <int>, 'subject': <str>, 'created_on': <datetime>}]
    """
    try:

        today = datetime.date.today()
        resp = list(Post.objects.filter(valid_till__gt=today).values('id', 'subject', 'created_on'))

        for post in resp:
            post['total_votes'] = Vote.objects.filter(post_id=post['id']).count()

        return JsonResponse(resp, safe=False)

    except Exception as error:
        error_log().delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@login_required
def post_home(request, post_id):
    return render(request, 'post_home.html')


@login_required
def get_post_options(request, post_id):
    """
    :param request:
    :param post_id:
    :return: {
        'title': <str>,
        'created_on': <datetime>,
        'options': [{'id': <int>, 'title': <str>, 'link': <str>}]
    }
    """
    try:
        post = Post.objects.get(id=post_id)

        options = list(post.options.values('id', 'title', 'link'))

        resp = {'title': post.title, 'created_on': post.created_on, 'options': options}

        return JsonResponse(resp, safe=True)

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)


@login_required
def vote(request, post_id):
    """
    request data = {'option_id': <int>}
    :param request:
    :param post_id:
    :return: None
    """

    try:
        data = json.loads(request.body)
        option_id = data['option_id']

        assert Post.objects.get(
            id=post_id).valid_till.date() > datetime.date.today(), 'This post is now closed for voting.'
        assert Vote.objects.filter(post_id=post_id, user_id=request.user.id).count() == 0, 'Already voted'

        Vote(post_id=post_id, option_id=option_id, user_id=request.user.id).save()

        return HttpResponse()

    except Exception as error:
        error_log.delay(request.path, request.META['REMOTE_ADDR'], str(traceback.format_exc()))
        return HttpResponseBadRequest(error)
