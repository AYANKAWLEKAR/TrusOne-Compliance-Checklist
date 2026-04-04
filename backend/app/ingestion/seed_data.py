SEED_DOCUMENTS = [
    {
        "title": "OSHA Process Safety Management of Highly Hazardous Chemicals",
        "source_url": "https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.119",
        "agency": "OSHA",
        "regulation_id": "29 CFR 1910.119",
        "jurisdiction": "federal",
        "state": None,
        "county": None,
        "industry_sectors": ["chemical manufacturing", "petrochemicals", "specialty chemicals"],
        "min_employee_size": 11,
        "max_employee_size": None,
        "effective_date": "1992-02-24",
        "full_text": (
            "The employer shall establish and implement written operating procedures that provide "
            "clear instructions for safely conducting activities involved in each covered process. "
            "Employees involved in operating a process shall be trained in an overview of the process, "
            "its hazards, and the operating procedures. Incident investigations must be promptly "
            "initiated and retained. Compliance audits shall be certified at least every three years."
        ),
        "extra_metadata": {"source_type": "seed"},
        "required_document_types": ["SOPs", "training records", "audit logs", "corrective action documentation"],
        "required_workflows": ["training management", "incident tracking", "internal audit", "document control"],
    },
    {
        "title": "EPA Risk Management Program Requirements",
        "source_url": "https://www.ecfr.gov/current/title-40/chapter-I/subchapter-C/part-68",
        "agency": "EPA",
        "regulation_id": "40 CFR Part 68",
        "jurisdiction": "federal",
        "state": None,
        "county": None,
        "industry_sectors": ["chemical manufacturing", "petrochemicals"],
        "min_employee_size": 1,
        "max_employee_size": None,
        "effective_date": "1996-06-20",
        "full_text": (
            "Covered facilities must maintain a risk management plan, document hazard assessments, "
            "establish prevention program procedures, and investigate incidents. Mechanical integrity "
            "requirements imply inspection records, maintenance documentation, and operating procedures."
        ),
        "extra_metadata": {"source_type": "seed"},
        "required_document_types": ["risk assessments", "SOPs", "audit logs"],
        "required_workflows": ["incident tracking", "document control", "internal audit"],
    },
    {
        "title": "California Hazardous Materials Business Plan Guidance",
        "source_url": "https://calepa.ca.gov/",
        "agency": "California DTSC",
        "regulation_id": "CA HMBP Guidance",
        "jurisdiction": "state",
        "state": "CA",
        "county": "Alameda",
        "industry_sectors": ["chemical manufacturing", "warehousing"],
        "min_employee_size": 1,
        "max_employee_size": None,
        "effective_date": "2024-01-01",
        "full_text": (
            "Facilities handling hazardous materials in California should maintain current site maps, "
            "inventory records, emergency response procedures, and staff training documentation. "
            "Local administering agencies may review business plans, inspections, and retention practices."
        ),
        "extra_metadata": {"source_type": "seed"},
        "required_document_types": ["quality manual", "training records", "risk assessments"],
        "required_workflows": ["training management", "document control", "incident tracking"],
    },
]
