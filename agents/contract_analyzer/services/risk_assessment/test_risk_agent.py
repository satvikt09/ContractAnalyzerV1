from agents.contract_analyzer.services.risk_assessment.risk_agent import (
    generate_risk_table
)

sample_results = [

    {
        "clause": "Bank Guarantees",
        "requirement": "Performance Guarantee not exceeding 10%",
        "status": "Not Met",
        "evidence": "Performance security obligations total 12%",
        "remarks": "Total guarantee obligations exceed 10%"
    },

    {
        "clause": "Payment Terms",
        "requirement": "All payments Net 30 days from invoice",
        "status": "Partially Met",
        "evidence": "30-day period starts after acceptance and reconciliation",
        "remarks": "Not strictly Net 30 from invoice"
    },

    {
        "clause": "Insurance",
        "requirement": "Insurance responsibilities defined",
        "status": "Met",
        "evidence": "Insurance obligations clearly defined",
        "remarks": "Requirement satisfied"
    }

]

risk_table = generate_risk_table(
    sample_results
)

for row in risk_table:

    print("\n")
    print("=" * 50)

    for k, v in row.items():

        print(f"{k}: {v}")