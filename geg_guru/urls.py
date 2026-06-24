"""Root URL config for the standalone custom-dev scaffold."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
from django.contrib import admin
# pyrefly: ignore [missing-import]
from django.urls import include, path

from guru import views as guru_views
from guru.api_views import ask_question, upload_contract, remove_uploaded_file, upload_progress

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("login/", guru_views.login, name="login"),
    path("", guru_views.workspace_sample_agent, name="workspace_sample_agent"),
    path("api/download-report/",guru_views.download_report,name="download_report"),
    path("api/download-table-docx/", guru_views.download_table_docx, name="download_table_docx"),
    path("api/upload/",upload_contract),
    path("api/upload-progress/", upload_progress),
    path("api/chat/",ask_question),
    path("api/remove_file/", remove_uploaded_file),
]
