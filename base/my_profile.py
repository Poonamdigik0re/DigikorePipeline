from PIL import Image
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.shortcuts import render


@login_required
def home(request):
    profile = request.user.userprofile

    if request.FILES:
        profile_picture = File(request.FILES['profile_picture'])
        profile.profile_picture = profile_picture
        profile.save()
        profile_picture.close()

        # update poster size
        try:
            image = Image.open(profile.profile_picture.path)
            image.thumbnail((300, 300))
            image.save(profile.profile_picture.path)
        except:
            pass

    data = {
        'full_name': profile.full_name,
        'date_of_birth': profile.date_of_birth.strftime('%b %d, %Y'),
        'date_of_joining': profile.date_of_joining.strftime('%b %d, %Y'),
        'designation': profile.designation.name,
        'department': profile.department.name,
        'pan': profile.pan,
        'bank_details': profile.bank_details,

        'email': profile.email,
        # 'personal_email': profile.personal_email,
        'address': profile.address,
        'phone': profile.phone,
        'emergency_contact': profile.emergency_contact,
        'profile_picture': profile.profile_picture.url if profile.profile_picture else "/static/img/default_profile.png"
    }

    return render(request, 'my_profile.html', {'data': data})
