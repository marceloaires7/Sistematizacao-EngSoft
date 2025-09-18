# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    # Inclui todas as URLs do app 'hotel' na raiz do site
    path("", include("hotel.urls", namespace="hotel")),
]
