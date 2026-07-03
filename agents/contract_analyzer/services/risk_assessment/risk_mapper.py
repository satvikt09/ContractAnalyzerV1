def get_rag(status: str) -> str:
    """Map compliance status to a RAG rating."""
    status = status.lower()
    if status == "met":
        return "Green"
    if status == "partially met":
        return "Amber"
    return "Red"