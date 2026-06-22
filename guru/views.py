"""Cutout view stub for a ped_c-style conversational workspace."""

from __future__ import annotations

from django.shortcuts import redirect, render
from django.http import FileResponse
from django.utils import timezone
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
def download_report(request):

    return FileResponse(
        open(
            "contract_analysis_report.docx",
            "rb"
        ),
        as_attachment=True,
        filename="Contract_Analysis_Report.docx"
    )