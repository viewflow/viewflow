from django.conf.urls import url
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect


def users(request):
    return {
        'users': User.objects.filter(is_active=True).order_by('-username')
    }


def login_as(request):
    user = None

    user_pk = request.GET.get('user_pk', None)
    if user_pk:
        try:
            user = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            pass

    if user:
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
    else:
        logout(request)

    return redirect('/')


urlpatterns = [
    url(r'^login_as/$', login_as, name="login_as")
]
