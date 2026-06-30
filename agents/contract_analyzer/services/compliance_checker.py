import json
import time
# pyrefly: ignore [missing-import]
from ollama import chat
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents.contract_analyzer.services.checklist_requirements_benchmark import (
    CHECKLIST_REQUIREMENTS
)

from agents.contract_analyzer.services.compliance_rule_engine import (
    evaluate_compliance_rules
)
from agents.contract_analyzer.services.risk_signals import (
    contains_risk_signal
)
from .clause_summary import (
    generate_clause_summary
)
from .config import (
    SHOW_CLAUSE_SUMMARY_COLUMN,
    SHOW_HISTORICAL_ACTION_COLUMN
)

def get_relevant_sentences(content, keywords):

    sentences = content.split(".")

    relevant = []

    for sentence in sentences:

        sentence_lower = sentence.lower()

        if any(
            keyword in sentence_lower
            for keyword in keywords
        ):
            relevant.append(sentence)

    return ". ".join(relevant)


def evaluate_requirement_with_ollama(
    requirement,
    classified_clauses
):

    matching_clauses = []

    clause_name = (
        requirement["clause"]
        .lower()
    )

    matching_clauses = []

    for clause in classified_clauses:

        if clause["clause_type"] == "payment" and clause_name == "Payment Terms":
            matching_clauses.append(clause)

        elif clause["clause_type"] == "bank_guarantees" and clause_name == "Bank Guarantees":
            matching_clauses.append(clause)

        elif clause["clause_type"] == "liquidated_damages" and clause_name == "Liquidated Damages":
            matching_clauses.append(clause)

        elif clause["clause_type"] == "warranties" and clause_name == "Guarantee":
            matching_clauses.append(clause)

        elif clause["clause_type"] == "termination" and clause_name == "Termination":
            matching_clauses.append(clause)

        elif clause["clause_type"] == "suspension" and clause_name == "Suspension":
            matching_clauses.append(clause)

        elif clause["clause_type"] == "insurance" and clause_name == "Insurance":
            matching_clauses.append(clause)

        elif clause["clause_type"] == "liability" and clause_name == "Liability":
            matching_clauses.append(
                clause
            )

    if not matching_clauses:

        matching_clauses = (
            classified_clauses
        )

    print(
        f"\nRequirement: "
        f"{requirement['requirement']}"
    )

    print(
        f"Matching Clauses: "
        f"{len(matching_clauses)}"
    )
    compact_clauses = []

    for c in matching_clauses:

        compact_clauses.append(
            {
                "title": c["title"],
                "content": c["content"][:2500]
            }
        )


    prompt = f"""
    You are a senior enterprise contract compliance analyst.
    Your task is to evaluate contractual compliance against a checklist.
    Clause Category:
    {clause_name}
    Requirements:
    {json.dumps(requirement, indent=2)}
    Contract Clauses:
    {json.dumps(matching_clauses, indent=2)}
    ANALYSIS INSTRUCTIONS
    Analyze EACH requirement independently.
    Do NOT assume a requirement is satisfied merely because
    a related clause exists.
    For every requirement:

    1. Find supporting evidence.
    2. Compare percentages.
    3. Compare monetary limits.
    4. Compare dates.
    5. Compare durations.
    6. Compare obligations.
    7. Compare liability allocations.
    8. Compare approval requirements.
    9. Compare exclusions.
    10. Compare carve-outs.
    11. Compare exceptions.
    12. Compare conditions.
    13. Compare scope limitations.
    14. Compare alternative remedies.
    15. Compare recovery reductions.
    16. Compare trigger events.
    17. Compare applicability restrictions.

    ==================================================
    STATUS DEFINITIONS
    ==================

    Status MUST be exactly one of:

    Met
    Partially Met
    Not Met

    Never return:

    Fully Met
    Mostly Met
    Compliant
    Non-Compliant
    Pass
    Fail

    ==================================================
    MET
    ===

    Return Met only when:

    * The requirement is fully satisfied.
    * No material exception exists.
    * No material carve-out exists.
    * No material limitation exists.
    * No conditional dependency weakens protection.
    * No alternative mechanism reduces the intended benefit.

    ==================================================
    PARTIALLY MET
    =============
    A requirement should be marked Partially Met when:

    - the requirement technically exists
    - but its protection is reduced through:
    - exclusions
    - carve-outs
    - conditions
    - limited applicability
    - discretionary rights
    - approval dependencies
    - reduced recovery mechanisms
    - alternative remedies
    - deemed provisions

    Even if the requirement is present,
    reduced protection should result in
    Partially Met rather than Met.
    
    Return Partially Met when the requirement exists
    but protection is weakened by:

    * exceptions
    * exclusions
    * carve-outs
    * conditional obligations
    * approval dependencies
    * limited applicability
    * named-party restrictions
    * reduced coverage
    * reduced recovery
    * salvage deductions
    * alternative remedies
    * discretionary rights
    * deemed events
    * secondary triggers
    * additional prerequisites
    * scope limitations
    * liability exclusions
    * operational restrictions

    Examples:

    Requirement:
    45% Minimum Advance

    Clause:
    30% immediately + 15% after conditions

    Result:
    Partially Met

    Reason:
    Requirement exists but access to full benefit
    depends on additional conditions.

    ---

    Requirement:
    Force Majeure applies to subcontractors

    Clause:
    Applies only to approved Tier-1 suppliers

    Result:
    Partially Met

    Reason:
    Protection exists but applicability is restricted.

    ---

    Requirement:
    Insurance covers equipment at buyer premises

    Clause:
    Coverage exists but unloading and internal shifting
    are excluded

    Result:
    Partially Met

    Reason:
    Coverage exists but important exclusions reduce protection.

    ---

    Requirement:
    Consequential damages excluded

    Clause:
    Consequential damages excluded but numerous
    exceptions exist

    Result:
    Partially Met

    Reason:
    Protection exists but carve-outs materially weaken it.

    ==================================================
    NOT MET
    =======

    Return Not Met when:

    * Requirement is absent.
    * Requirement directly conflicts with contract wording.
    * Required percentage is exceeded.
    * Required limit is breached.
    * Required obligation is missing.
    * Contract position is materially different.

    Examples:

    Requirement:
    Performance Guarantee not exceeding 10%

    Clause:
    10% PBG + 2% bridge guarantee

    Result:
    Not Met

    ---

    Requirement:
    Aggregate LD capped at 5%

    Clause:
    Aggregate cap is 7.5%

    Result:
    Not Met

    ==================================================
    IMPORTANT
    =========

    Do not invent facts.

    Do not infer obligations that are not present.

    Use only information contained in the supplied clauses.

    If evidence contains:

    * except
    * excluding
    * unless
    * subject to
    * however
    * notwithstanding
    * limited to
    * only
    * provided that
    * salvage deduction
    * deemed
    * approval required

    carefully determine whether the requirement
    should be Partially Met.

    A requirement may be technically present but still
    be Partially Met because the protection has been
    reduced.

    ==================================================
    OUTPUT FORMAT
    =============

    Return ONLY a JSON ARRAY.

    Example:

    [
    {{
    "clause": "Payment Terms",
    "requirement": "45% Minimum Advance",
    "status": "Partially Met",
    "evidence": "30% advance immediately, remaining 15% subject to conditions",
    "remarks": "Advance payment split across conditional milestones",
    "location": "00511.2.1",
    "confidence": 0.95
    }}
    ]

    Do not include markdown.
    Do not include explanations.
    Return valid JSON only.
    """


    start_time = time.time()
    print("CALLING OLLAMA...")
    response = chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )
    print("OLLAMA RETURNED")

    print(
        f"Ollama Time: "
        f"{round(time.time() - start_time, 2)} sec"
    )

    text = (
        response["message"]["content"]
        .replace(
            "```json",
            ""
        )
        .replace(
            "```",
            ""
        )
        .strip()
    )

    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end <= start:

        raise Exception(
            "No JSON found"
        )

    return json.loads(
        text[start:end]
    )

def compress_clause(text):

    important = []

    keywords = [
        "%",
        "day",
        "days",
        "payment",
        "invoice",
        "termination",
        "cancel",
        "suspend",
        "liability",
        "warranty",
        "guarantee",
        "insurance"
    ]

    sentences = text.split(".")

    for sentence in sentences:

        if any(
            k in sentence.lower()
            for k in keywords
        ):
            important.append(
                sentence.strip()
            )

    return ". ".join(
        important[:10]
    )

def evaluate_group_with_ollama(
    clause_name,
    requirements,
    classified_clauses
):

    CLAUSE_MAP = {
        "Payment Terms": "payment",
        "Bank Guarantees": "bank_guarantees",
        "Liquidated Damages": "liquidated_damages",
        "Guarantee": "warranties",
        "Termination": "termination",
        "Suspension": "suspension",
        "Insurance": "insurance",
        "Liability": "liability"
    }

    matching_clauses = []

    for c in classified_clauses:

        if c["clause_type"] != CLAUSE_MAP.get(clause_name):
            continue

        content = compress_clause(
            c["content"]
        )

        if clause_name == "Payment Terms":

            content = get_relevant_sentences(
                content,
                [
                    "payment",
                    "invoice",
                    "invoicing",
                    "billing",
                    "30 day",
                    "30 days",
                    "lot",
                    "partial"
                ]
            )

        matching_clauses.append(
            {
                "title": c["title"],
                "content": content,
                "full_content":
                    c["content"][:6000]
            }
        )

    print("\nCLAUSES SENT TO OLLAMA:")

    for c in matching_clauses:
        print(c["title"])

    prompt = f"""
    Clause Group:
    {clause_name}

    Requirements:
    {json.dumps(requirements, indent=2)}

    Contract Clauses:
    {json.dumps(matching_clauses, indent=2)}

    Evaluate every requirement independently.

    IMPORTANT:

    For EACH requirement perform the following process:

    STEP 1:
    Identify the exact benchmark requirement.

    STEP 2:
    Locate the exact clause text supporting or contradicting it.

    STEP 3:
    Compare:

    - percentages
    - numbers
    - durations
    - carve-outs
    - exclusions
    - exceptions
    - deemed provisions
    - conditional obligations
    - approval requirements
    - scope limitations
    - dates
    - obligations
    - conditions
    - approvals
    - exceptions
    - carve-outs
    - exclusions

    STEP 4:
    Decide status.

    Met:
    Requirement fully satisfied with no material deviation.

    Partially Met:
    Requirement exists but contains:
    - conditions
    - approvals
    - exceptions
    - carve-outs
    - reduced scope
    - additional obligations
    - modified triggers

    Not Met:
    Requirement missing OR materially different.

    IMPORTANT EXAMPLES

    Requirement:
    45% Minimum Advance

    Clause:
    30% advance immediately and 15% only after conditions

    Result:
    Partially Met

    Requirement:
    Performance Guarantee not exceeding 10%

    Clause:
    10% PBG plus additional 2% bridge guarantee

    Result:
    Not Met

    Requirement:
    61-90 day cancellation fee = 40%

    Clause:
    61-90 day fee = 38%

    Result:
    Not Met

    Requirement:
    Partial delivery and invoicing allowed

    Clause:
    Lot-wise delivery and invoicing permitted

    Result:
    Met
    IMPORTANT:

    Allowed statuses ONLY:

    - Met
    - Partially Met
    - Not Met

    Never return:

    - Fully Met
    - Mostly Met
    - Needs Review
    - Compliant
    - Non-Compliant

    Definitions:

    Met:
    Requirement is completely satisfied.

    Partially Met:
    Requirement exists but includes:
    - conditions
    - exceptions
    - carve-outs
    - limitations
    - additional obligations
    - modified triggers
    - reduced scope

    Not Met:
    Requirement is absent or materially different.

    You must compare:

    - percentages
    - numbers
    - dates
    - durations
    - obligations
    - exclusions
    - limitations
    - carve-outs
    - conditions

    Evaluate EACH requirement separately.

    Do not let one requirement influence another.

    Return ONLY a JSON array.
    Example:

    [
      {{
        "clause":"Payment Terms",
        "requirement":"45% Minimum Advance",
        "status":"Partially Met",
        "evidence":"",
        "remarks":"",
        "confidence":0.95
      }}
    ]
    """
    start = time.time()
    print(
        f"{clause_name} prompt size:",
        len(prompt)
    )
    response = chat(
        model="gemma4:31b-cloud",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )

    print(
        f"{clause_name} took "
        f"{round(time.time()-start,2)} sec"
    )
    text = (
        response["message"]["content"]
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    start = text.find("[")
    end = text.rfind("]") + 1

    return json.loads(
        text[start:end]
    )

def check_compliance(
    classified_clauses
):
    try:
        from agents.contract_analyzer.services.historical_indexing import initialize_index
        initialize_index()
    except Exception as e:
        print(f"Error initializing historical index: {e}")

    overall_start = time.time()
    print("\n" + "=" * 60)
    print("RULE COMPLIANCE ENGINE")
    print("=" * 60)

    rule_start = time.time()

    rule_output = (
        evaluate_compliance_rules(
            CHECKLIST_REQUIREMENTS,
            classified_clauses
        )
    )

    rule_time = round(
        time.time() - rule_start,
        2
    )

    rule_results = (
        rule_output["rule_results"]
    )

    unresolved_requirements = (
        rule_output[
            "unresolved_requirements"
        ]
    )

    print(
        f"Rule Results: "
        f"{len(rule_results)}"
    )

    print(
        f"Unresolved Requirements: "
        f"{len(unresolved_requirements)}"
    )

    print("\n" + "=" * 60)
    print("UNRESOLVED REQUIREMENTS")
    print("=" * 60)

    for req in unresolved_requirements:

        print(
            f"{req['clause']} | "
            f"{req['requirement']}"
        )

    print("=" * 60)

    if not unresolved_requirements:

        print(
            "\nAll requirements solved by rules."
        )

        return rule_results

    llm_results = []
    ollama_start = time.time()
    print("\nSAMPLE CLAUSE OBJECT\n")

    print(
        json.dumps(
            classified_clauses[2],
            indent=2
    )
)
    print("\n" + "=" * 60)
    print("STARTING OLLAMA EVALUATION")
    print("=" * 60)

    grouped_requirements = {}

    for req in unresolved_requirements:

        clause = req["clause"]

        if clause not in grouped_requirements:
            grouped_requirements[clause] = []

        grouped_requirements[clause].append(req)
   

    with ThreadPoolExecutor(max_workers=4) as executor:

        future_map = {}

        for clause_name, requirements in grouped_requirements.items():

            future = executor.submit(
                evaluate_group_with_ollama,
                clause_name,
                requirements,
                classified_clauses
            )

            future_map[future] = clause_name

        for future in as_completed(future_map):

            clause_name = future_map[future]

            print(
                f"\nCompleted Group: {clause_name}"
            )

            try:

                results = future.result()

                llm_results.extend(
                    results
                )

                for result in results:

                    print(
                        f"{result['requirement']} "
                        f"-> "
                        f"{result['status']}"
                    )

            except Exception as e:

                print(
                    f"Failed group: {clause_name}"
                )

                print(e)

                for req in grouped_requirements[clause_name]:

                    llm_results.append(
                        {
                            "clause": req["clause"],
                            "requirement": req["requirement"],
                            "status": "Not Met",
                            "evidence": "",
                            "remarks": f"Evaluation failed: {e}",
                            "confidence": 0.0
                        }
                    )
    ollama_time = round(
        time.time() - ollama_start,
        2
    )
    print("\n" + "=" * 60)
    print("LLM RESULTS")
    print("=" * 60)
    print(
        f"Count: "
        f"{len(llm_results)}"
    )

    final_results = (
        rule_results
        + llm_results
    )
    
    clause_map = {}
    for clause in classified_clauses:
        clause_type = clause.get(
            "clause_type",
            ""
        )
        if clause_type not in clause_map:
            clause_map[clause_type] = []
        clause_map[clause_type].append(
            clause.get(
                "content",
                ""
            )
        )    
    CLAUSE_TO_TYPE = {
        "Payment Terms":
            "payment",
        "Bank Guarantees":
            "bank_guarantees",
        "Liquidated Damages":
            "liquidated_damages",
        "Guarantee":
            "warranties",
        "Force Majeure":
            "force_majeure",
        "Termination":
            "termination",
        "Suspension":
            "suspension",
        "Change Orders":
            "change_orders",
        "Governing Law":
            "governing_law",
        "Dispute Resolution":
            "governing_law",
        "Insurance":
            "insurance",
        "Liability":
            "liability",
        "Consequential Damages":
            "consequential_damages",
        "Critical Sub-Suppliers":
            "force_majeure"
    }     
    if SHOW_CLAUSE_SUMMARY_COLUMN:
        for result in final_results:
            clause_type = (
                CLAUSE_TO_TYPE.get(
                    result["clause"],
                    ""
                )
            )
            clause_text = " ".join(
                clause_map.get(
                    clause_type,
                    []
                )
            )
            result["clause_summary"] = (
                generate_clause_summary(
                    clause_text
                )
            ) 
            print(
                result["clause"],
                "summary length:",
                len(
                    result["clause_summary"]
                )
            )           
    # --------------------------------
    # RISK SIGNAL ENRICHMENT
    # --------------------------------

    for i, result in enumerate(final_results):

        text = (
            f"{result.get('evidence', '')} "
            f"{result.get('remarks', '')}"
        )

        signals = contains_risk_signal(
            text
        )

        result["risk_signals"] = signals

        result["risk_candidate"] = (
            result["status"] != "Met"
            or len(signals) >= 2
            or len(
                result.get("remarks","")
                ) > 120
            )

        result["score"] = (
            100
            if result["status"] == "Met"
            else 60
            if result["status"] == "Partially Met"
            else 0
        )

    # Process Historical Actions Taken Column dynamically in batches with caching and retry constraints
    if SHOW_HISTORICAL_ACTION_COLUMN:
        from agents.contract_analyzer.services.similarity_retrieval import retrieve_historical_records
        from agents.contract_analyzer.services.historical_summary_generator import (
            get_cache_key, SUMMARY_CACHE, batch_generate_historical_summaries, NO_HISTORICAL_CASES_FOUND_STRING
        )
        
        print(f"\nPROCESSING HISTORICAL ACTIONS FOR {len(final_results)} COMPLIANCE ROWS...")
        hist_start = time.time()
        
        to_summarize = []
        for idx, res in enumerate(final_results):
            c_name = res.get("clause", "")
            req_text = res.get("requirement", "")
            status = res.get("status", "")
            
            # Check module-level in-memory cache first
            cache_key = get_cache_key(c_name, req_text)
            if cache_key in SUMMARY_CACHE:
                res["historical_action"] = SUMMARY_CACHE[cache_key]
                continue
                
            # Perform similarity lookup
            records = retrieve_historical_records(c_name, req_text)
            if not records:
                res["historical_action"] = NO_HISTORICAL_CASES_FOUND_STRING
                SUMMARY_CACHE[cache_key] = res["historical_action"]
            else:
                to_summarize.append({
                    "id": idx,
                    "clause": c_name,
                    "requirement": req_text,
                    "status": status,
                    "records": records
                })
                
        # Group into batches of size 8
        batch_size = 8
        batches = [to_summarize[i : i + batch_size] for i in range(0, len(to_summarize), batch_size)]
        
        if batches:
            print(f"Generating historical actions for {len(to_summarize)} rows in {len(batches)} batches (max 2 concurrent LLM calls)...")
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = {executor.submit(batch_generate_historical_summaries, b): b for b in batches}
                for future in as_completed(futures):
                    try:
                        batch_res = future.result()
                        for row_idx, summary_text in batch_res.items():
                            final_results[row_idx]["historical_action"] = summary_text
                    except Exception as e:
                        print(f"Batch generation failed: {e}")
                        # Fallback for the batch
                        batch = futures[future]
                        for item in batch:
                            row_idx = item["id"]
                            records = item["records"]
                            if records and len(records) > 0:
                                from agents.contract_analyzer.services.historical_summary_generator import format_historical_action_with_references
                                fallback_action = records[0].get("historical_action") or "Revised contract language during review."
                                final_results[row_idx]["historical_action"] = format_historical_action_with_references(fallback_action, [records[0]])
                            else:
                                final_results[row_idx]["historical_action"] = NO_HISTORICAL_CASES_FOUND_STRING
                                
        print(f"Historical Actions retrieval and batch generation took {round(time.time() - hist_start, 2)} seconds.")
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(
        f"Count: "
        f"{len(final_results)}"
    )

    total_time = round(
        time.time() - overall_start,
        2
    )

    print("\n" + "=" * 60)
    print("TIMING SUMMARY")
    print("=" * 60)

    print(f"Rule Engine : {rule_time} sec")
    print(f"Ollama Total: {ollama_time} sec")
    print(f"Total Run   : {total_time} sec")

    print("=" * 60)

    print("\nSAMPLE RESULT")
    print(final_results[0])

    return final_results