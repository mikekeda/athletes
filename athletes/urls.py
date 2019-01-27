"""
Athletes URL Configuration
"""
from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from django.utils.translation import ugettext_lazy as _

from api.urls import router


urlpatterns = [
    path('', include('core.urls', namespace='core')),
    path('api/', include('api.urls', namespace='api')),
    path('api/', include(router.urls)),
    path('admin/', admin.site.urls),
]

admin.site.site_header = _('Athletes administration')


if settings.DEBUG:
    from django.conf.urls.static import static
    import debug_toolbar

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
