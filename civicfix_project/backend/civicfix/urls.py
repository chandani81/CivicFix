from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from ai_services.views import ReverseGeocodeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/departments/", include("departments.urls")),
    path("api/complaints/", include("complaints.urls")),
    path("api/chatbot/", include("ai_services.urls")),
    path("api/location/reverse/", ReverseGeocodeView.as_view(), name="location-reverse"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
