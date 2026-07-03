import re
import time
import json
import logging
# pyrefly: ignore [missing-import]
from ollama import chat

logger = logging.getLogger(__name__)

SUMMARY_CACHE = {}

NO_HISTORICAL_CASES_FOUND_STRING = (
    "Historical Action:\n"
    "No similar historical case found.\n\n"
    "Historical Reference:\n"
    "N/A"
)

def get_cache_key(clause, requirement):
    """Generates a standardized key for cache lookups."""
    return (str(clause).lower().strip(), str(requirement).lower().strip())

def format_historical_action_with_references(historical_action_summary, sources):
    """
    Formats the historical action summary and its sources as a structured string.
    """
    if not sources:
        return f"{historical_action_summary}\n\nHistorical Reference:\nN/A"
    
    seen = set()
    unique_sources = []
    for s in sources:
        if not s:
            continue
        file_source = s.get("file_source", "").strip()
        clause = s.get("clause", "").strip()
        if not file_source:
            continue
        key = (file_source.lower(), clause.lower())
        if key not in seen:
            seen.add(key)
            unique_sources.append(s)
            
    unique_sources = unique_sources[:3]
    
    if not unique_sources:
        return f"{historical_action_summary}\n\nHistorical Reference:\nN/A"
        
    ref_parts = []
    if len(unique_sources) == 1:
        src = unique_sources[0]
        file_name = src.get("file_source", "").strip()
        clause_val = src.get("clause", "").strip()
        req_val = src.get("requirement", "").strip()
        sec_sub = src.get("section_subclause", "").strip()
        quote_val = src.get("quote", "").strip()
        
        ref_parts.append("Source:")
        ref_parts.append(file_name)
        
        if sec_sub and sec_sub.lower() != "n/a" and sec_sub != "":
            if clause_val.lower() in sec_sub.lower():
                clause_line = f"Clause: {sec_sub}"
            else:
                clause_line = f"Clause: {sec_sub} – {clause_val}"
        else:
            clause_line = f"Clause: {clause_val}"
        ref_parts.append(clause_line)
        
        if req_val and req_val.lower() != "n/a" and req_val != "":
            ref_parts.append(f"Requirement: {req_val}")
            
        if quote_val and quote_val.lower() != "n/a" and quote_val != "":
            if not (quote_val.startswith('"') and quote_val.endswith('"')) and not (quote_val.startswith("'") and quote_val.endswith("'")):
                quote_val = f'"{quote_val}"'
            ref_parts.append(f"\nQuote:\n{quote_val}")
    else:
        ref_parts.append("Sources:")
        for src in unique_sources:
            file_name = src.get("file_source", "").strip()
            clause_val = src.get("clause", "").strip()
            sec_sub = src.get("section_subclause", "").strip()
            
            if sec_sub and sec_sub.lower() != "n/a" and sec_sub != "":
                if clause_val.lower() in sec_sub.lower():
                    clause_display = sec_sub
                else:
                    clause_display = f"{sec_sub} – {clause_val}"
            else:
                clause_display = clause_val
                
            ref_parts.append(f"• {file_name} – {clause_display}")
            
    reference_string = "\n".join(ref_parts)
    return f"{historical_action_summary}\n\nHistorical Reference\n{reference_string}"

def chat_with_backoff(model, messages, options=None):
    """
    Executes a chat completion call with automatic retry and exponential backoff
    on failure (2s -> 4s -> 8s) up to 4 attempts.
    """
    backoff = 2
    for attempt in range(4):
        try:
            response = chat(model=model, messages=messages, options=options)
            return response
        except Exception as e:
            logger.warning(f"Ollama chat call failed on attempt {attempt + 1}: {e}")
            if attempt == 3:
                raise e
            logger.info(f"Retrying in {backoff} seconds...")
            time.sleep(backoff)
            backoff *= 2

def batch_generate_historical_summaries(batch_items):
    """
    Synthesizes historical action summaries for a batch of items (typically 5-10 rows).
    Each item is a dictionary containing:
      - 'id': unique identifier or index
      - 'clause': category name
      - 'requirement': requirement text
      - 'status': current compliance status
      - 'records': list of matching historical database entries
    Returns a dictionary mapping the item ID/index to its generated summary string.
    """
    if not batch_items:
        return {}

    # Format the batch items into the prompt context
    formatted_items = []
    for item in batch_items:
        records_str = []
        for idx, rec in enumerate(item["records"]):
            sec_sub = rec.get("section_subclause") or "N/A"
            records_str.append(
                f"  Record {idx+1}:\n"
                f"    - Source Filename: {rec['file_source']}\n"
                f"    - Matching Clause: {rec['clause']}\n"
                f"    - Matching Requirement: {rec['requirement']}\n"
                f"    - Matching Section/Sub-clause: {sec_sub}\n"
                f"    - Status: {rec['status']}\n"
                f"    - Evidence: {rec['evidence']}\n"
                f"    - Remarks: {rec['remarks']}\n"
                f"    - Action Taken: {rec['historical_action']}\n"
                f"    - Resolution: {rec.get('resolution') or 'N/A'}\n"
            )
        
        formatted_items.append({
            "id": item["id"],
            "clause": item["clause"],
            "requirement": item["requirement"],
            "current_status": item["status"],
            "historical_data_found": "\n".join(records_str) if records_str else "No prior records"
        })

    prompt = f"""
    You are a senior enterprise contract compliance consultant.
    You are given a list of current contract requirements and their corresponding historical review contexts.
    For each requirement, generate a concise "Historical Action Taken" summary (exactly 1 to 2 sentences) describing what was typically done or negotiated in the past for this requirement.
    Also, identify the most relevant 1-3 sources that contributed to the summary, and include a short supporting quote (exactly 1 sentence only) from the retrieved historical report if possible.
    
    Requirements Batch:
    {json.dumps(formatted_items, indent=2)}
    
    INSTRUCTIONS:
    1. Read the historical reviews context for each requirement.
    2. Write a concise 1–2 sentence summary explaining the typical negotiations or revisions made historically.
    3. Do not copy past remarks or actions verbatim; write a natural, coherent summary.
    4. Focus only on the facts in the historical reviews.
    5. Choose the most relevant 1-3 sources that contributed to the summary. Avoid duplicate references.
    6. For each source, keep track of:
       - file_source: the filename (e.g. Contract_Analysis_Report_07.docx)
       - clause: the matching clause name (e.g. Liquidated Damages)
       - requirement: the matching requirement text
       - section_subclause: matching section/sub-clause if available (e.g. Clause 5.4)
       - quote: a short supporting quote (exactly 1 sentence only) from the evidence, remarks, or action taken of that source that directly supports the generated summary (if possible).
    
    CRITICAL SCHEMA RULE:
    You MUST return ONLY a valid JSON object matching the following schema. Do not write any markdown blocks, comments, or intro/outro texts.
    {{
      "summaries": [
        {{
          "id": 0,
          "historical_action": "Concise 1-2 sentence summary of what was negotiated historically...",
          "sources": [
            {{
              "file_source": "Contract_Analysis_Report_07.docx",
              "clause": "Liquidated Damages",
              "requirement": "Aggregate LD capped at 5%",
              "section_subclause": "Clause 5.4",
              "quote": "The aggregate liquidated damages cap was revised to 5% before final execution."
            }}
          ]
        }},
        ...
      ]
    }}
    """

    results_map = {}
    try:
        response = chat_with_backoff(
            model="gemma4:31b-cloud",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }

            ],
            options={
                "temperature": 0.1
            }
        )
        
        content_text = response["message"]["content"].strip()
        
        # Strip markdown code blocks if the model wrapped the JSON
        start_obj = content_text.find("{")
        end_obj = content_text.rfind("}") + 1
        if start_obj != -1 and end_obj > start_obj:
            content_text = content_text[start_obj:end_obj]
            
        parsed_response = json.loads(content_text)
        for entry in parsed_response.get("summaries", []):
            item_id = entry.get("id")
            action_text = entry.get("historical_action", "").strip()
            sources = entry.get("sources", [])
            if item_id is not None and action_text:
                results_map[item_id] = format_historical_action_with_references(action_text, sources)

    except Exception as e:
        logger.error(f"Error processing batched summaries: {e}")
        # Fall back to single-record summaries for this batch to ensure code stability

    # Populate any missing IDs with a safe fallback to prevent broken columns
    for item in batch_items:
        item_id = item["id"]
        if item_id not in results_map:
            records = item["records"]
            if records and len(records) > 0:
                summary_text = records[0].get("historical_action") or "Revised contract language during review."
                results_map[item_id] = format_historical_action_with_references(summary_text, [records[0]])
            else:
                results_map[item_id] = NO_HISTORICAL_CASES_FOUND_STRING

    # Cache the newly generated summaries in the persistent SUMMARY_CACHE
    for item in batch_items:
        item_id = item["id"]
        key = get_cache_key(item["clause"], item["requirement"])
        SUMMARY_CACHE[key] = results_map[item_id]

    return results_map


def generate_clause_historical_actions(clause_name, sub_requirements, historical_records):
    """
    Generates unique historical actions for all sub-requirements under a main clause using a single LLM call.
    """
    if not sub_requirements:
        return {}

    # Format historical records
    formatted_docs = []
    for idx, rec in enumerate(historical_records):
        sec_sub = rec.get("section_subclause") or "N/A"
        formatted_docs.append(
            f"  Document {idx+1}:\n"
            f"    - Source Filename: {rec['file_source']}\n"
            f"    - Matching Clause: {rec['clause']}\n"
            f"    - Matching Requirement: {rec['requirement']}\n"
            f"    - Matching Section/Sub-clause: {sec_sub}\n"
            f"    - Status: {rec['status']}\n"
            f"    - Evidence: {rec['evidence']}\n"
            f"    - Remarks: {rec['remarks']}\n"
            f"    - Action Taken: {rec['historical_action']}\n"
            f"    - Resolution: {rec.get('resolution') or 'N/A'}\n"
        )

    # Format sub-requirements
    formatted_reqs = []
    for req in sub_requirements:
        formatted_reqs.append({
            "id": req["id"],
            "requirement": req["requirement"],
            "status": req["status"],
            "current_evidence": req.get("evidence") or "",
            "current_remarks": req.get("remarks") or ""
        })

    docs_text = "\n".join(formatted_docs) if formatted_docs else "No historical records found for this clause."
    sample_id = next(iter(sub_requirements))["id"] if sub_requirements else 0

    prompt = f"""
    You are a senior enterprise contract compliance consultant.
    You are analyzing historical records to generate "Historical Action Taken" entries for a batch of sub-requirements under the main clause: "{clause_name}".
    
    Here are the retrieved historical documents relevant to "{clause_name}":
    {docs_text}
    
    Here is the list of current sub-requirements to evaluate:
    {json.dumps(formatted_reqs, indent=2)}
    
    INSTRUCTIONS:
    1. For each sub-requirement, review the historical documents to find cases that match the sub-requirement's specific objective.
    2. Generate a unique, concise "Historical Action Taken" summary (exactly 1 to 2 sentences) describing what was typically done, negotiated, or revised in the past specifically for this sub-requirement.
    3. Do not reuse or duplicate the exact same summary or text across sibling requirements. Each sub-requirement must have its own custom summary reflecting its specific requirement text.
    4. If no similar historical case exists for a specific sub-requirement, output a safe generic default or state that no historical records were found.
    5. For each sub-requirement, identify up to 3 most relevant source references from the historical documents. Do not duplicate references.
    6. For each source reference, include:
       - file_source: the exact matching file_source from the document.
       - clause: the exact matching clause from the document.
       - requirement: the exact matching requirement from the document.
       - section_subclause: section/sub-clause of the document.
       - quote: a short quote (exactly 1 sentence only) from the document's evidence, remarks, or action taken that directly supports the historical action summary.
       
    CRITICAL SCHEMA RULE:
    You MUST return ONLY a valid JSON object matching the following schema. Do not write any markdown code blocks (such as ```json), comments, or intro/outro texts.
    
    {{
      "results": [
        {{
          "id": {sample_id},
          "historical_action": "Concise 1-2 sentence summary of what was negotiated historically for this specific requirement...",
          "sources": [
            {{
              "file_source": "Contract_Analysis_Report_07.docx",
              "clause": "Payment Terms",
              "requirement": "45% Minimum Advance",
              "section_subclause": "Clause 4.1",
              "quote": "The advance payment requirement was accepted as 45% upon initial delivery of spec sheets."
            }}
          ]
        }}
      ]
    }}
    """

    results_map = {}
    try:
        response = chat_with_backoff(
            model="gemma4:31b-cloud",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.1
            }
        )
        
        content_text = response["message"]["content"].strip()
        
        # Strip markdown code blocks if the model wrapped the JSON
        start_obj = content_text.find("{")
        end_obj = content_text.rfind("}") + 1
        if start_obj != -1 and end_obj > start_obj:
            content_text = content_text[start_obj:end_obj]
            
        parsed_response = json.loads(content_text)
        for entry in parsed_response.get("results", []):
            item_id = entry.get("id")
            action_text = entry.get("historical_action", "").strip()
            sources = entry.get("sources", [])
            if item_id is not None and action_text:
                results_map[item_id] = format_historical_action_with_references(action_text, sources)

    except Exception as e:
        logger.error(f"Error processing clause-level batched summaries for {clause_name}: {e}")

    # Fallback populating
    for req in sub_requirements:
        item_id = req["id"]
        if item_id not in results_map:
            # Try to match the closest record for this specific requirement using the input historical records
            matched_rec = None
            if historical_records:
                from agents.contract_analyzer.services.similarity_retrieval import compute_similarity
                best_score = -1
                for rec in historical_records:
                    score = compute_similarity(clause_name, req["requirement"], rec["clause"], rec["requirement"])
                    if score > best_score:
                        best_score = score
                        matched_rec = rec
            if matched_rec:
                summary_text = matched_rec.get("historical_action") or "Revised contract language during review."
                results_map[item_id] = format_historical_action_with_references(summary_text, [matched_rec])
            else:
                results_map[item_id] = NO_HISTORICAL_CASES_FOUND_STRING

    # Cache results
    for req in sub_requirements:
        item_id = req["id"]
        key = get_cache_key(clause_name, req["requirement"])
        SUMMARY_CACHE[key] = results_map[item_id]

    return results_map
