from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import HttpResponse

def health_check(request):
    """Lightweight endpoint for keep-alive pings"""
    return HttpResponse("OK", content_type="text/plain")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('dashboard:home')),
    path('accounts/', include('accounts.urls')),
    path('health/', health_check, name='health_check'),
    path('leaves/', include('leaves.urls')),
    path('dashboard/', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)