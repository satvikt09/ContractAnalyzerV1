"""Root URL config for the standalone custom-dev scaffold."""

from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

from guru import views as guru_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("login/", guru_views.login, name="login"),
    path("", guru_views.workspace_sample_agent, name="workspace_sample_agent"),
        path("download-report/",guru_views.download_report,name="download_report"),
]
