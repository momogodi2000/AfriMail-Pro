"""
Main URL Configuration for AfriMail Pro
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('backend.urls')),
    path('api/', include('backend.api_urls')),  # API endpoints
    path('favicon.ico', RedirectView.as_view(url='/static/images/favicon.ico')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar URLs
    urlpatterns = [
        path('__debug__/', include('debug_toolbar.urls')),
        path('__reload__/', include('django_browser_reload.urls')),
    ] + urlpatterns

# Customize admin
admin.site.site_header = "AfriMail Pro Administration"
admin.site.site_title = "AfriMail Pro Admin"
admin.site.index_title = "Welcome to AfriMail Pro Administration"
admin.site.site_url = "/"