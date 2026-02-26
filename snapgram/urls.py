from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('chat/', include('chat.urls')),
]

# Serve media files locally in dev (Cloudinary handles it in production)
if hasattr(settings, 'MEDIA_ROOT'):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
