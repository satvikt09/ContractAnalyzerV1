import re
import sqlite3
import logging
from agents.contract_analyzer.services.historical_indexing import get_db_connection

logger = logging.getLogger(__name__)

STOPWORDS = {
    "and", "or", "to", "the", "a", "of", "in", "from", "for", "is", 
    "at", "on", "with", "by", "not", "be", "all", "its", "each", "any", "are"
}

def tokenize(text):
    """Converts text to lowercase, removes punctuation, and splits into a set of words, excluding stopwords."""
    if not text:
        return set()
    words = re.findall(r"\b\w+\b", text.lower())
    return {w for w in words if w not in STOPWORDS}

def get_jaccard_similarity(text1, text2):
    """Computes Jaccard similarity (intersection over union) of token sets."""
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    if not tokens1 or not tokens2:
        return 0.0
    return len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2))

def get_char_ngrams(text, n=3):
    """Generates a set of character n-grams from text."""
    if not text:
        return set()
    text_clean = re.sub(r"\s+", " ", text.lower().strip())
    if len(text_clean) < n:
        return {text_clean}
    return {text_clean[i:i+n] for i in range(len(text_clean) - n + 1)}

def get_ngram_similarity(text1, text2, n=3):
    """Computes Jaccard similarity of character n-grams."""
    ngrams1 = get_char_ngrams(text1, n)
    ngrams2 = get_char_ngrams(text2, n)
    if not ngrams1 or not ngrams2:
        return 0.0
    return len(ngrams1.intersection(ngrams2)) / len(ngrams1.union(ngrams2))

def normalize_clause_name(name):
    """Maps and normalizes variant clause names to standard comparable categories."""
    if not name:
        return ""
    name_clean = name.lower().replace("_", " ").replace("-", " ").strip()
    
    mappings = {
        "payment": "payment terms",
        "bank guarantees": "bank guarantees",
        "liquidated damages": "liquidated damages",
        "guarantee": "guarantee warranties",
        "warranties": "guarantee warranties",
        "termination": "termination",
        "suspension": "suspension",
        "insurance": "insurance",
        "liability": "liability limitations limitation"
    }
    
    for key, mapped in mappings.items():
        if key in name_clean or name_clean in key:
            return mapped
            
    return name_clean

def extract_section_subclause(clause_text):
    """Extracts clause/section identifiers (e.g. Clause 5.4, Section 12, 5.4.1) if available."""
    if not clause_text:
        return ""
    pattern = r'\b(?:Clause|Section)\s*\d+(?:\.\d+)*\b|\b\d+(?:\.\d+)+\b'
    match = re.search(pattern, clause_text, re.IGNORECASE)
    if match:
        return match.group(0).strip()
    return ""

def compute_similarity(q_clause, q_req, db_clause, db_req):
    """
    Computes a combined similarity score between the query and database entry.
    Clause name alignment is required; requirement similarity uses both word tokens and character trigrams.
    """
    norm_q_clause = normalize_clause_name(q_clause)
    norm_db_clause = normalize_clause_name(db_clause)
    
    # Calculate clause similarity first
    clause_sim = get_jaccard_similarity(norm_q_clause, norm_db_clause)
    
    # If the clauses are completely unrelated, don't match
    if clause_sim < 0.2:
        return 0.0
        
    # Requirement similarity
    req_token_sim = get_jaccard_similarity(q_req, db_req)
    req_trigram_sim = get_ngram_similarity(q_req, db_req, n=3)
    req_sim = 0.5 * req_token_sim + 0.5 * req_trigram_sim
    
    # Combine scores (80% weight to requirement text similarity, 20% to clause category alignment)
    return 0.2 * clause_sim + 0.8 * req_sim

def retrieve_historical_records(query_clause, query_req, threshold=0.35, max_results=3):
    """
    Queries the database and performs a similarity search.
    Returns up to max_results records with similarity >= threshold.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT clause, requirement, status, evidence, remarks, historical_action, resolution, file_source
        FROM historical_cases
    """)
    rows = cursor.fetchall()
    conn.close()
    
    scored_records = []
    for row in rows:
        db_clause = row["clause"]
        db_req = row["requirement"]
        
        score = compute_similarity(query_clause, query_req, db_clause, db_req)
        
        if score >= threshold:
            # Extract section/subclause from db_clause
            sec_sub = extract_section_subclause(db_clause)
            
            scored_records.append({
                "clause": db_clause,
                "requirement": db_req,
                "status": row["status"],
                "evidence": row["evidence"],
                "remarks": row["remarks"],
                "historical_action": row["historical_action"],
                "resolution": row["resolution"],
                "file_source": row["file_source"],
                "section_subclause": sec_sub if sec_sub else "N/A",
                "similarity_score": score
            })
            
    # Sort by similarity score descending
    scored_records.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    return scored_records[:max_results]
