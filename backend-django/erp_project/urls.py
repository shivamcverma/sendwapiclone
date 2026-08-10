from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.views.generic import TemplateView
from apps.messaging.views import dashboard


def home(request):
    return HttpResponse("✅ Server is running!")


urlpatterns = [
    path('', home, name='home'),

    path('admin/', admin.site.urls),

    path('api/accounts/', include('apps.accounts.urls')),

    path('api/whatsapp/', include('apps.messaging.urls')),

    path('whatsapp/', include('apps.messaging.urls')),

    path(
        'register/',
        TemplateView.as_view(
            template_name='accounts/register.html'
        ),
        name='register'
    ),

    path(
        'login/',
        TemplateView.as_view(
            template_name='accounts/login.html'
        ),
        name='login'
    ),

    path(
        'user/dashboard/',
        dashboard,
        name='user_dashboard'
    ),

    path(
        'admin/dashboard/',
        TemplateView.as_view(
            template_name='admin/dashboard.html'
        ),
        name='admin_dashboard'
    ),
]