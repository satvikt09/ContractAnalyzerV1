def get_rag(status):

    status = status.lower()

    if status == "met":
        return "Green"

    if status == "partially met":
        return "Amber"

    return "Red"