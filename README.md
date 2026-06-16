# Cutout scaffold

This folder contains a ready-to-fill scaffold for shipping a new conversational agent into the `geg_guru` app. It mirrors the `ped_c` workspace structure so the contributor only has to fill the marked blanks and copy the files back into the main codebase.

## What is included
- Standalone Django shell: `manage.py`, `geg_guru/settings.py`, `geg_guru/urls.py`, `geg_guru/wsgi.py` for local runs.
- `requirements.txt` – minimal deps (Django, boto3, optional PyMuPDF/textract).
- `agents/sample_agent/` – Python skeleton for a Claude Sonnet-based chat agent (PDF-first, image fallback), with TODOs for ingestion, retrieval, and chat logic.
- `guru/templates/guru/workspace_sample_agent.html` – Page layout matching the app (sidebar, header, chat shell). Only the inner workspace card is meant to be customized.
- `guru/templates/guru/layouts/sidebar_layout.html` + `guru/templates/guru/base.html` – lightweight layout clone with logo and structure.
- `guru/static/guru/css/base.css`, `guru/static/guru/img/logo.svg`, `guru/static/guru/js/workspace_sample_agent.js` – styling/assets to resemble the platform.
- `guru/views.py` – Drop-in view stub to be copied into the main `guru/views.py` once filled.

## How to use
1) Install deps: `pip install -r requirements.txt` (inside `custom-dev/`). This includes `boto3/botocore`; optional extras like PyMuPDF and textract are listed for PDF/image handling.
2) Duplicate/rename: Copy `agents/sample_agent` to your agent name (e.g., `agents/my_agent`), and rename the template/static filenames similarly.
3) Fill the blanks:
   - Wire PDF/text extraction and image fallback in `chat_agent.py` (see TODOs).
   - Implement chunking + embedding + retrieval; currently placeholders store files only.
   - Replace the default Bedrock model ARN with the target Claude 3.7 Sonnet ARN if it differs.
   - Keep AWS keys/region sourced from `os.environ` (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, optional `BEDROCK_MODEL_ID`).
4) Front-end: Update `workspace_sample_agent.html` to your desired inner layout while keeping `{% extends "guru/layouts/sidebar_layout.html" %}` for standardized chrome. Point any XHR/fetch URLs to `https://` endpoints to stay SSL-safe.
5) Run locally (from `custom-dev/`):
   ```
   export AWS_REGION=ap-south-1
   export AWS_ACCESS_KEY_ID=...   # provided credential
   export AWS_SECRET_ACCESS_KEY=...   # provided credential
   # optional: export BEDROCK_MODEL_ID=arn:aws:bedrock:ap-south-1::foundation-model/anthropic.claude-3-7-sonnet-20250219-v1:0
   python3 manage.py migrate
   python3 manage.py runserver 127.0.0.1:8501
   ```
   This starts Django with sqlite; PDFs/DOCs are handled via textract/PyMuPDF if installed.
6) Ship back: Once validated, drop the filled agent folder, template, static JS, and view snippet into the main codebase; add the route to the main `geg_guru/guru/urls.py` and keep HTTPS for production.

## Notes
- The scaffold avoids hard-coded credentials; everything pulls from environment variables.
- Keep file size/type checks aligned with your use case and update `ALLOWED_EXTENSIONS`, `MAX_UPLOAD_FILES`, and `MAX_UPLOAD_BYTES` accordingly.
- If you introduce background tasks or additional endpoints, document them here and ensure they remain HTTPS-compatible for production.
- The included logo/CSS are lightweight clones to mimic the platform; swap them out if your branding differs.

## Microsoft OAuth (Entra ID) scaffold
The cutout now mirrors the production Microsoft OAuth setup (django-allauth + custom adapter).

1) Install the extra dependency: `pip install -r requirements.txt` (adds `django-allauth`).
2) Export env vars (no keys are hard-coded):
   ```
   export AZURE_CLIENT_ID=...
   export AZURE_TENANT_ID=...
   export AZURE_CLIENT_SECRET=...
   export ENFORCE_GLOBAL_LOGIN=1   # optional: enforce auth on all routes
   ```
3) Run migrations so `django_site` exists, then start the server.
4) Visit `/login/` for the SSO button (or hit `/accounts/microsoft/login/` directly).

The adapter lives in `guru/adapters.py`, middleware in `guru/middleware.py`, and the login
template in `guru/templates/guru/login.html`.
