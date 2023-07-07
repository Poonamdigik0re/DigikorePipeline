from django.contrib.auth.decorators import permission_required
from django.shortcuts import render


@permission_required('base.attendance')
def home(request):
    return render(request, 'attendance.html')
