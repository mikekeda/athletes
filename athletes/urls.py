"""
Athletes URL Configuration
"""
from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from django.utils.translation import ugettext_lazy as _


urlpatterns = [
    path('', include('core.urls', namespace='core')),
    path('admin/', admin.site.urls),
]

admin.site.site_header = _('Athletes administration')


if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
