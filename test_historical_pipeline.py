import os
import sys
import sqlite3
from pathlib import Path

# Add the workspace root to path if needed
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from agents.contract_analyzer.services.historical_indexing import initialize_index, DB_PATH
from agents.contract_analyzer.services.similarity_retrieval import retrieve_historical_records
from agents.contract_analyzer.services.historical_summary_generator import batch_generate_historical_summaries

def test_pipeline():
    print("Step 1: Running historical index initialization...")
    initialize_index()
    
    print("\nStep 2: Checking SQLite database records...")
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database file {DB_PATH} not found.")
        return
        
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM historical_cases")
    total_cases = cursor.fetchone()[0]
    print(f"Total historical cases in DB: {total_cases}")
    
    cursor.execute("SELECT filename, last_modified FROM metadata")
    metadata_files = cursor.fetchall()
    print("Metadata files in DB:")
    for fn, mtime in metadata_files:
        print(f"  - {fn}: {mtime}")
        
    if total_cases == 0:
        print("WARNING: No historical cases parsed.")
        conn.close()
        return

    # Let's inspect a few rows
    cursor.execute("SELECT clause, requirement, status, historical_action FROM historical_cases LIMIT 3")
    sample_rows = cursor.fetchall()
    print("\nSample historical cases in DB:")
    for idx, row in enumerate(sample_rows):
        print(f"  Case {idx+1}:")
        print(f"    Clause: {row[0]}")
        print(f"    Requirement: {row[1]}")
        print(f"    Status: {row[2]}")
        print(f"    Action: {row[3][:100]}...")
        
    conn.close()
    
    print("\nStep 3: Testing retrieval...")
    test_cases = [
        ("Payment Terms", "45% Minimum Advance"),
        ("Termination", "Cancellation fee structure defined"),
        ("Liability", "Consequential Damages")
    ]
    
    retrieved_items = []
    for clause, req in test_cases:
        print(f"\nRetrieving for: Clause='{clause}', Req='{req}'")
        records = retrieve_historical_records(clause, req)
        print(f"Found {len(records)} matches.")
        for r in records:
            print(f"  - Similarity: {round(r['similarity_score'], 3)}")
            print(f"    Source: {r['file_source']}")
            print(f"    Matched Clause: {r['clause']}")
            print(f"    Matched Req: {r['requirement']}")
            print(f"    Section/Sub-clause: {r.get('section_subclause')}")
            print(f"    Hist Action: {r['historical_action'][:100]}...")
            
        if records:
            retrieved_items.append({
                "id": len(retrieved_items),
                "clause": clause,
                "requirement": req,
                "status": "Partially Met",
                "records": records
            })
            
    print("\nStep 4: Testing batch LLM summarization...")
    if not retrieved_items:
        print("No items retrieved to summarize.")
        return
        
    print(f"Summarizing {len(retrieved_items)} items...")
    summaries = batch_generate_historical_summaries(retrieved_items)
    print("\nGenerated Summaries with Historical References:")
    for item_id, text in summaries.items():
        original_item = retrieved_items[item_id]
        print("="*60)
        print(f"Clause: '{original_item['clause']}' - Req: '{original_item['requirement']}'")
        print("="*60)
        print(text)
        print()

if __name__ == "__main__":
    test_pipeline()
