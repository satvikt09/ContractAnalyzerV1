# pyrefly: ignore [missing-import]
from django.http import JsonResponse
# pyrefly: ignore [missing-import]
from django.views.decorators.csrf import csrf_exempt

from agents.contract_analyzer import (
    chat_agent as sample_agent
)
from agents.contract_analyzer.services.config import (
    SHOW_EXECUTIVE_SUMMARY,
    SHOW_CLAUSE_SUMMARY_COLUMN,
    SHOW_STATUS_COLUMN,
    SHOW_HISTORICAL_ACTION_COLUMN
)

import json

from agents.contract_analyzer import (
    chat_agent as sample_agent
)

@csrf_exempt
def ask_question(request):
    if request.method != "POST":
        return JsonResponse(
            {
                "error":
                "POST required"
            },
            status=405
        )

    try:

        data = json.loads(
            request.body
        )

        if not request.session.session_key:

            request.session.create()

        session_key = (
            request.session.session_key
        )

        result = (
            sample_agent.answer_question(
                session_key,
                data["message"]
            )
        )

        return JsonResponse(
            {
                "answer":
                result.get(
                    "answer",
                    ""
                )
            }
        )

    except Exception as e:

        return JsonResponse(
            {
                "error":
                str(e)
            },
            status=500
        )
    
@csrf_exempt
def upload_contract(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "error": "POST required"
            },
            status=405
        )

    try:

        if not request.session.session_key:

            request.session.create()

        session_key = (
            request.session.session_key
        )

        print(
            "SESSION:",
            session_key
        )

        uploads = request.FILES.getlist(
            "files"
        )

        result = (
            sample_agent.index_uploaded_files(
                session_key,
                uploads
            )
        )

        print(
            "RESULT TYPE:",
            type(result)
        )

        result["session_key"] = session_key

        result["config"] = {
            "showExecutiveSummary":
                SHOW_EXECUTIVE_SUMMARY,
            "showClauseSummaryColumn":
                SHOW_CLAUSE_SUMMARY_COLUMN,
            "showStatusColumn":
                SHOW_STATUS_COLUMN,
            "showHistoricalActionColumn":
                SHOW_HISTORICAL_ACTION_COLUMN
        }
        
        return JsonResponse(
            result,
            json_dumps_params={
                "default": str
            }
        )

    except Exception as e:

        import traceback

        traceback.print_exc()
        
        try:
            with open("debug_error.log", "w") as f:
                traceback.print_exc(file=f)
        except Exception:
            pass

        return JsonResponse(
            {
                "error": str(e)
            },
            status=500
        )

@csrf_exempt
def remove_uploaded_file(request):
    if request.method != "POST":
        return JsonResponse(
            {
                "error": "POST required"
            },
            status=405
        )
    try:
        data = json.loads(request.body)
        filename = data.get("filename", "")
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        result = sample_agent.remove_uploaded_file(
            session_key,
            filename
        )
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse(
            {
                "error": str(e)
            },
            status=500
        )

@csrf_exempt
def upload_progress(request):
    session_key = request.GET.get("session_key")
    if not session_key:
        session_key = request.session.session_key
    
    state = sample_agent._ensure_session(session_key)
    return JsonResponse({
        "progress_message": getattr(state, "progress_message", "Initializing...")
    })
