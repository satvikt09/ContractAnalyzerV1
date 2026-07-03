# Contract Analyser

An AI-powered, configuration-driven Contract Analyser designed to automate enterprise contract review using a modular multi-agent architecture.

The tool analyzes uploaded contracts, validates business compliance requirements, identifies contractual risks, recommends mitigation strategies, retrieves historical actions from previous contract reviews, and generates comprehensive reports. Its configuration-driven design enables horizontal deployment across multiple Business Units without modifying the core application.

# Features

- AI-powered contract analysis
- PDF contract upload
- Digital PDF text extraction (PyMuPDF)
- Automatic clause segmentation
- Rule-based clause classification
- Configuration-driven compliance validation
- Multi-Agent AI workflow
    - Compliance Analysis
    - Risk Assessment
    - Mitigation Recommendation
- Historical Action Retrieval with references and supporting quotes
- Executive Summary generation
- Export reports in DOCX, PDF and CSV formats
- Responsive React dashboard
- Live processing status updates
- Modular architecture for multiple Business Units

# Installation

## Backend

`pip install -r requirements.txt`


Run migrations:
`python manage.py migrate`

Start server:
`python manage.py runserver`


## Frontend

`cd frontend`

`npm install`

`npm run dev`


# Reports

The platform generates

## Individual Reports

- Compliance Table
- Risk Assessment Table
- Mitigation Recommendation Table

Each report can be downloaded as

- DOCX
- PDF
- CSV

## Complete Report

Includes

- Executive Summary
- Compliance Table
- Risk Assessment
- Mitigation Recommendations
- Historical Actions

Available in

- DOCX
- PDF
