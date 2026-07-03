import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from ollama import chat

from agents.contract_analyzer.services.checklist_requirements_benchmark import CHECKLIST_REQUIREMENTS
from agents.contract_analyzer.services.compliance_rule_engine import evaluate_compliance_rules
from agents.contract_analyzer.services.risk_signals import contains_risk_signal
from .config import SHOW_CLAUSE_SUMMARY_COLUMN, SHOW_HISTORICAL_ACTION_COLUMN


def get_relevant_sentences(content: str, keywords: list[str]) -> str:
    """Filter sentences containing any of the specified keywords."""
    sentences = content.split(".")
    relevant = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in keywords):
            relevant.append(sentence)
    return ". ".join(relevant)


def evaluate_requirement_with_ollama(requirement: dict, classified_clauses: list) -> dict:
    """Evaluate contract compliance for a single requirement using Ollama."""
    clause_name = requirement["clause"].lower()
    matching_clauses = []

    for clause in classified_clauses:
        c_type = clause["clause_type"]
        if c_type == "payment" and clause_name == "Payment Terms":
            matching_clauses.append(clause)
        elif c_type == "bank_guarantees" and clause_name == "Bank Guarantees":
            matching_clauses.append(clause)
        elif c_type == "liquidated_damages" and clause_name == "Liquidated Damages":
            matching_clauses.append(clause)
        elif c_type == "warranties" and clause_name == "Guarantee":
            matching_clauses.append(clause)
        elif c_type == "termination" and clause_name == "Termination":
            matching_clauses.append(clause)
        elif c_type == "suspension" and clause_name == "Suspension":
            matching_clauses.append(clause)
        elif c_type == "insurance" and clause_name == "Insurance":
            matching_clauses.append(clause)
        elif c_type == "liability" and clause_name == "Liability":
            matching_clauses.append(clause)

    if not matching_clauses:
        matching_clauses = classified_clauses

    print(f"\nRequirement: {requirement['requirement']}")
    print(f"Matching Clauses: {len(matching_clauses)}")

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
    print("CALLING OLLAMA...")
    response = chat(
        model="qwen3:8b",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )
    print("OLLAMA RETURNED")

    text = response["message"]["content"].replace("```json", "").replace("```", "").strip()
    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end <= start:
        raise Exception("No JSON found")

    return json.loads(text[start:end])


def compress_clause(text: str) -> str:
    """Extract sentences containing contract keywords for analysis."""
    important = []
    keywords = [
        "%", "day", "days", "payment", "invoice", "termination",
        "cancel", "suspend", "liability", "warranty", "guarantee", "insurance"
    ]
    sentences = text.split(".")
    for sentence in sentences:
        if any(k in sentence.lower() for k in keywords):
            important.append(sentence.strip())
    return ". ".join(important[:10])


def evaluate_group_with_ollama(clause_name: str, requirements: list, classified_clauses: list) -> list:
    """Evaluate contract compliance for a group of requirements using Ollama."""
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

        content = compress_clause(c["content"])
        if clause_name == "Payment Terms":
            content = get_relevant_sentences(
                content,
                ["payment", "invoice", "invoicing", "billing", "30 day", "30 days", "lot", "partial"]
            )

        matching_clauses.append({
            "title": c["title"],
            "content": content,
            "full_content": c["content"][:6000]
        })

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
    print(f"{clause_name} prompt size:", len(prompt))
    response = chat(
        model="gemma4:31b-cloud",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )

    text = response["message"]["content"].replace("```json", "").replace("```", "").strip()
    start = text.find("[")
    end = text.rfind("]") + 1

    return json.loads(text[start:end])


def check_compliance(classified_clauses: list) -> list:
    """Check contract compliance using rule engine and Ollama for unresolved requirements."""
    try:
        from agents.contract_analyzer.services.historical_indexing import initialize_index
        initialize_index()
    except Exception as e:
        print(f"Error initializing historical index: {e}")

    print("\n" + "=" * 60)
    print("RULE COMPLIANCE ENGINE")
    print("=" * 60)

    rule_output = evaluate_compliance_rules(CHECKLIST_REQUIREMENTS, classified_clauses)
    rule_results = rule_output["rule_results"]
    unresolved_requirements = rule_output["unresolved_requirements"]

    print(f"Rule Results: {len(rule_results)}")
    print(f"Unresolved Requirements: {len(unresolved_requirements)}")

    print("\n" + "=" * 60)
    print("UNRESOLVED REQUIREMENTS")
    print("=" * 60)

    for req in unresolved_requirements:
        print(f"{req['clause']} | {req['requirement']}")
    print("=" * 60)

    if not unresolved_requirements:
        print("\nAll requirements solved by rules.")
        return rule_results

    llm_results = []
    print("\nSAMPLE CLAUSE OBJECT\n")
    print(json.dumps(classified_clauses[2], indent=2))
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
            print(f"\nCompleted Group: {clause_name}")
            try:
                results = future.result()
                llm_results.extend(results)
                for result in results:
                    print(f"{result['requirement']} -> {result['status']}")
            except Exception as e:
                print(f"Failed group: {clause_name}")
                print(e)
                for req in grouped_requirements[clause_name]:
                    llm_results.append({
                        "clause": req["clause"],
                        "requirement": req["requirement"],
                        "status": "Not Met",
                        "evidence": "",
                        "remarks": f"Evaluation failed: {e}",
                        "confidence": 0.0
                    })

    print("\n" + "=" * 60)
    print("LLM RESULTS")
    print("=" * 60)
    print(f"Count: {len(llm_results)}")

    final_results = rule_results + llm_results

    if SHOW_CLAUSE_SUMMARY_COLUMN:
        for result in final_results:
            req_name = result.get("requirement", "")
            evidence = result.get("evidence", "").strip()
            status = result.get("status", "")

            if not evidence:
                if status == "Not Met":
                    summary_text = f"Requirement not met: No supporting provisions or evidence found in the contract for '{req_name}'."
                else:
                    summary_text = f"Requirement '{req_name}' evaluated with status '{status}' (no specific evidence text recorded)."
            else:
                sentences = [
                    s.strip()
                    for s in evidence.replace("\n", " ").replace("\t", " ").split(".")
                    if len(s.strip()) > 10
                ]
                if sentences:
                    joined = ". ".join(sentences[:3])
                    if not joined.endswith("."):
                        joined += "."
                    summary_text = f"Provisions regarding '{req_name}': {joined}"
                else:
                    summary_text = f"Provisions regarding '{req_name}': {evidence}"

            result["clause_summary"] = summary_text
            print(result["clause"], "requirement summary length:", len(result["clause_summary"]))

    # Enrich compliance results with risk signals.
    for result in final_results:
        text = f"{result.get('evidence', '')} {result.get('remarks', '')}"
        signals = contains_risk_signal(text)
        result["risk_signals"] = signals
        result["risk_candidate"] = (
            result["status"] != "Met"
            or len(signals) >= 2
            or len(result.get("remarks", "")) > 120
        )
        result["score"] = (
            100 if result["status"] == "Met"
            else 60 if result["status"] == "Partially Met"
            else 0
        )

    # Process Historical Actions Taken dynamically with caching and ThreadPoolExecutor.
    if SHOW_HISTORICAL_ACTION_COLUMN:
        from agents.contract_analyzer.services.similarity_retrieval import retrieve_historical_records
        from agents.contract_analyzer.services.historical_summary_generator import (
            get_cache_key, SUMMARY_CACHE, generate_clause_historical_actions, NO_HISTORICAL_CASES_FOUND_STRING
        )

        print(f"\nPROCESSING HISTORICAL ACTIONS FOR {len(final_results)} COMPLIANCE ROWS...")

        grouped_by_clause = {}
        for idx, res in enumerate(final_results):
            c_name = res.get("clause", "")
            req_text = res.get("requirement", "")

            cache_key = get_cache_key(c_name, req_text)
            if cache_key in SUMMARY_CACHE:
                res["historical_action"] = SUMMARY_CACHE[cache_key]
                continue

            if c_name not in grouped_by_clause:
                grouped_by_clause[c_name] = []
            grouped_by_clause[c_name].append({
                "id": idx,
                "requirement": req_text,
                "status": res.get("status", ""),
                "evidence": res.get("evidence", ""),
                "remarks": res.get("remarks", "")
            })

        if grouped_by_clause:
            print(f"Generating historical actions for {len(grouped_by_clause)} clauses...")

            def process_clause_group(clause_name, sub_reqs):
                clause_records = []
                seen_records = set()
                for req in sub_reqs:
                    records = retrieve_historical_records(clause_name, req["requirement"])
                    for rec in records:
                        rec_key = (rec.get("file_source", ""), rec.get("requirement", ""), rec.get("clause", ""))
                        if rec_key not in seen_records:
                            seen_records.add(rec_key)
                            clause_records.append(rec)

                if not clause_records:
                    results_map = {}
                    for req in sub_reqs:
                        item_id = req["id"]
                        results_map[item_id] = NO_HISTORICAL_CASES_FOUND_STRING
                        key = get_cache_key(clause_name, req["requirement"])
                        SUMMARY_CACHE[key] = NO_HISTORICAL_CASES_FOUND_STRING
                    return results_map

                return generate_clause_historical_actions(clause_name, sub_reqs, clause_records)

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = {executor.submit(process_clause_group, name, reqs): name for name, reqs in grouped_by_clause.items()}
                for future in as_completed(futures):
                    clause_name = futures[future]
                    try:
                        clause_results = future.result()
                        for row_idx, summary_text in clause_results.items():
                            final_results[row_idx]["historical_action"] = summary_text
                    except Exception as e:
                        print(f"Failed historical actions for clause {clause_name}: {e}")
                        for req in grouped_by_clause[clause_name]:
                            row_idx = req["id"]
                            if "historical_action" not in final_results[row_idx]:
                                final_results[row_idx]["historical_action"] = NO_HISTORICAL_CASES_FOUND_STRING

    # Restore original checklist sorting order.
    order_map = {}
    for idx, item in enumerate(CHECKLIST_REQUIREMENTS):
        key = (item["clause"].strip().lower(), item["requirement"].strip().lower())
        if key not in order_map:
            order_map[key] = idx

    def get_order_key(res):
        clause = res.get("clause", "").strip().lower()
        req = res.get("requirement", "").strip().lower()
        key = (clause, req)
        if key in order_map:
            return order_map[key]
        for checklist_key, checklist_idx in order_map.items():
            if checklist_key[0] == clause and checklist_key[1] == req:
                return checklist_idx
        return 999999

    final_results.sort(key=get_order_key)

    print("\n" + "=" * 60)
    print("FINAL RESULTS (SORTED)")
    print("=" * 60)
    print(f"Count: {len(final_results)}")

    print("\nSAMPLE RESULT")
    print(final_results[0])

    return final_results