"""Cutout view stub for a ped_c-style conversational workspace."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
from django.shortcuts import redirect, render
# pyrefly: ignore [missing-import]
from django.http import FileResponse
# pyrefly: ignore [missing-import]
from django.utils import timezone
# pyrefly: ignore [missing-import]
from django.views.decorators.csrf import csrf_protect

from agents.contract_analyzer import chat_agent as sample_agent
from agents.contract_analyzer.services.config import (
    SHOW_EXECUTIVE_SUMMARY,
    SHOW_CLAUSE_SUMMARY_COLUMN,
    SHOW_STATUS_COLUMN
)

@csrf_protect
def workspace_sample_agent(request):

    session_key = (
        request.session.session_key
        or request.session.create()
    )

    context = {

        "nav_left_label":
            "Enterprise Contract Analyzer",

        "hero_title":
            "📄 AI-Powered Contract Review Platform",

        "hero_subtitle":
            "Upload contracts to automatically extract clauses, "
            "validate compliance requirements, identify risks "
            "and generate mitigation recommendations.",

        "uploaded_files":
            sample_agent.list_files(
                session_key
            ),

        "chat_history": [],

        "allowed_extensions":
            sorted(
                sample_agent.ALLOWED_EXTENSIONS
            ),

        "classified_clauses": [],

        "compliance_results": [],

        "risk_results": [],        

        "executive_summary": {},

        "show_status_column":
            SHOW_STATUS_COLUMN,

        "show_clause_summary_column":
            SHOW_CLAUSE_SUMMARY_COLUMN,

        "analysis_status":
            "Analysis status will be shown here"
    }

    if request.method == "POST":

        print("\n========== VIEW DEBUG ==========")

        print(
            "POST ACTION:",
            request.POST.get(
                "action"
            )
        )

        print(
            "FILES:",
            request.FILES
        )

        print(
            "================================\n"
        )

        action = request.POST.get(
            "action"
        )

        if action == "reset":

            sample_agent.reset_session(
                session_key
            )

            return redirect(
                request.path
            )

        if action == "remove_file":

            filename = (
                request.POST.get(
                    "filename"
                )
                or ""
            )

            outcome = (
                sample_agent.remove_uploaded_file(
                    session_key,
                    filename
                )
            )

            context["uploaded_files"] = (
                outcome.get(
                    "files",
                    []
                )
            )

        elif action == "upload":

            uploads = (
                request.FILES.getlist(
                    "files"
                )
            )

            try:

                result = (
                    sample_agent.index_uploaded_files(
                        session_key,
                        uploads
                    )
                )

                context["uploaded_files"] = (
                    result.get(
                        "files",
                        []
                    )
                )

                context["warnings"] = (
                    result.get(
                        "warnings",
                        []
                    )
                )

                context["sections"] = (
                    result.get(
                        "sections",
                        []
                    )
                )

                context["classified_clauses"] = (
                    result.get(
                        "classified_clauses",
                        []
                    )
                )

                context["compliance_results"] = (
                    result.get(
                        "compliance_results",
                        []
                    )
                )
                context["risk_results"] = (
                    result.get(
                        "risk_results",
                        []
                    )
                )
                context["mitigation_results"] = (
                    result.get(
                        "mitigation_results",
                        []
                    )
                )
                if SHOW_EXECUTIVE_SUMMARY:

                    context["executive_summary"] = (
                        result.get(
                            "executive_summary",
                            {}
                        )
                    )

                else:

                    context["executive_summary"] = {}                
                context["report_path"] = (
                    result.get(
                        "report_path"
                    )
                )
                context["analysis_status"] = (
                    "Compliance analysis completed"
                )

                print(
                    "Sections:",
                    len(
                        context["sections"]
                    )
                )

                print(
                    "Classified:",
                    len(
                        context[
                            "classified_clauses"
                        ]
                    )
                )

                print(
                    "Compliance:",
                    len(
                        context[
                            "compliance_results"
                        ]
                    )
                )
                print(
                    "Risk:",
                    len(
                        context[
                            "risk_results"
                        ]
                    )
                )
                print(
                    "Executive Summary:",
                    context.get(
                        "executive_summary",
                        {}
                    )
                )
            except Exception as err:

                context["error"] = str(
                    err
                )

                context["analysis_status"] = (
                    "Analysis failed"
                )

        elif action == "ask":

            message = (
                request.POST.get(
                    "message",
                    ""
                )
            )

            try:

                result = (
                    sample_agent.answer_question(
                        session_key,
                        message
                    )
                )

                context["chat_history"] = (
                    result.get(
                        "chat_history",
                        []
                    )
                )

                context["assistant_reply"] = (
                    result.get(
                        "answer",
                        ""
                    )
                )

                context["uploaded_files"] = (
                    sample_agent.list_files(
                        session_key
                    )
                )

            except Exception as err:

                context["error"] = str(
                    err
                )

    return render(
        request,
        "guru/workspace_sample_agent.html",
        context
    )

def login(request):

    return render(
        request,
        "guru/login.html"
    )
import io
import datetime

def download_report(request):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        with open("contract_analysis_report.docx", "rb") as f:
            data = f.read()
        buffer = io.BytesIO(data)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"Contract_Analysis_Report_{timestamp}.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# pyrefly: ignore [missing-import]
from django.http import JsonResponse

def download_table_docx(request):
    session_key = request.GET.get("session_key")
    if not session_key:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
    table_type = request.GET.get("type", "")
    
    from agents.contract_analyzer import chat_agent as sample_agent
    state = sample_agent._ensure_session(session_key)
    
    from agents.contract_analyzer.services.export.report_generator import (
        export_individual_compliance_report,
        export_individual_risk_report,
        export_individual_mitigation_report
    )
    
    buffer = io.BytesIO()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if table_type == "compliance":
        output_filename = f"Compliance_Evaluation_Report_{timestamp}.docx"
        export_individual_compliance_report(state.compliance_results, buffer)
    elif table_type == "risk":
        output_filename = f"Risk_Assessment_Report_{timestamp}.docx"
        export_individual_risk_report(state.risk_analysis, buffer)
    elif table_type == "mitigation":
        output_filename = f"Mitigation_Strategy_Guidelines_{timestamp}.docx"
        export_individual_mitigation_report(state.mitigation_analysis, buffer)
    else:
        return JsonResponse({"error": "Invalid table type"}, status=400)
        
    buffer.seek(0)
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=output_filename,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )