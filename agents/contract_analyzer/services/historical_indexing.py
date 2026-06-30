import os
import sqlite3
import logging
from pathlib import Path
from agents.contract_analyzer.services.historical_ingestion import parse_historical_docx

logger = logging.getLogger(__name__)

HISTORICAL_DATA_DIR = Path("c:/Satvik/vsCode/custom-dev/agents/contract_analyzer/historical_data")
DB_PATH = HISTORICAL_DATA_DIR / "historical_index.db"

def get_db_connection():
    """Returns a SQLite connection to the historical database."""
    HISTORICAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(conn):
    """Creates the necessary database tables if they do not exist."""
    cursor = conn.cursor()
    
    # Table to store historical cases
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clause TEXT,
            requirement TEXT,
            status TEXT,
            evidence TEXT,
            remarks TEXT,
            historical_action TEXT,
            resolution TEXT,
            file_source TEXT
        )
    """)
    
    # Table to cache processed file metadata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            filename TEXT PRIMARY KEY,
            last_modified REAL
        )
    """)
    conn.commit()

def initialize_index():
    """
    Scans the historical_data directory, syncs SQLite records with DOCX files on disk,
    and runs incremental ingestion.
    """
    logger.info("Initializing historical reports index...")
    conn = get_db_connection()
    create_tables(conn)
    
    cursor = conn.cursor()
    
    # Get current files on disk
    disk_files = {}
    if HISTORICAL_DATA_DIR.exists():
        for filename in os.listdir(str(HISTORICAL_DATA_DIR)):
            if filename.endswith(".docx") and filename != "contract_analysis_report.docx":
                file_path = HISTORICAL_DATA_DIR / filename
                disk_files[filename] = os.path.getmtime(str(file_path))
                
    # Get indexed files from metadata table
    cursor.execute("SELECT filename, last_modified FROM metadata")
    indexed_files = {row["filename"]: row["last_modified"] for row in cursor.fetchall()}
    
    # Identify changes
    files_to_delete = [f for f in indexed_files if f not in disk_files]
    files_to_index = []
    
    for f, mtime in disk_files.items():
        if f not in indexed_files or indexed_files[f] != mtime:
            files_to_index.append((f, mtime))
            
    # Process deletions
    if files_to_delete:
        logger.info(f"Removing indexed records for deleted files: {files_to_delete}")
        for f in files_to_delete:
            cursor.execute("DELETE FROM historical_cases WHERE file_source = ?", (f,))
            cursor.execute("DELETE FROM metadata WHERE filename = ?", (f,))
        conn.commit()
        
    # Process new/modified files
    for filename, mtime in files_to_index:
        logger.info(f"Ingesting file: {filename}")
        # Clean out old records if modifying
        cursor.execute("DELETE FROM historical_cases WHERE file_source = ?", (filename,))
        
        file_path = HISTORICAL_DATA_DIR / filename
        rows = parse_historical_docx(str(file_path))
        
        if rows:
            logger.info(f"Inserting {len(rows)} historical records from {filename}...")
            cursor.executemany("""
                INSERT INTO historical_cases (clause, requirement, status, evidence, remarks, historical_action, resolution, file_source)
                VALUES (:clause, :requirement, :status, :evidence, :remarks, :historical_action, :resolution, :file_source)
            """, rows)
            
        # Update metadata
        cursor.execute("""
            INSERT OR REPLACE INTO metadata (filename, last_modified)
            VALUES (?, ?)
        """, (filename, mtime))
        conn.commit()
        
    conn.close()
    logger.info("Historical index initialization complete.")
