"""Generate examples/sample_questionnaire.xlsx - a realistic vendor security questionnaire.

Questions are deliberately reworded vs. the answer library, and a few have
no approved answer at all, to show the SME-review guardrail.
"""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

QUESTIONS = [
    ("1.1", "Data Protection", "Is customer data encrypted while stored in your databases?"),
    ("1.2", "Data Protection", "What TLS version do you use to protect data in transit?"),
    ("1.3", "Data Protection", "Can we bring our own encryption keys?"),
    ("1.4", "Data Protection", "In which geographic regions is our data stored?"),
    ("2.1", "Access Control", "Does your platform support SSO via SAML 2.0 with Okta?"),
    ("2.2", "Access Control", "Can administrators enforce 2FA for all users?"),
    ("2.3", "Access Control", "Is SCIM user provisioning supported?"),
    ("2.4", "Access Control", "Describe how your staff access production environments."),
    ("3.1", "Compliance", "Please provide your most recent SOC 2 Type 2 report."),
    ("3.2", "Compliance", "Do you hold ISO/IEC 27001 certification?"),
    ("3.3", "Compliance", "Will you sign a BAA for HIPAA purposes?"),
    ("3.4", "Compliance", "Are you FedRAMP authorized?"),
    ("4.1", "Resilience", "What are your RPO and RTO targets?"),
    ("4.2", "Resilience", "How often are backups taken and how long are they kept?"),
    ("4.3", "Resilience", "What uptime do you guarantee?"),
    ("5.1", "Security Testing", "When was your last external pen test?"),
    ("5.2", "Security Testing", "Do you run a public bug bounty program?"),
    ("6.1", "Incident Response", "Within what timeframe will we be notified of a data breach?"),
    ("6.2", "People", "Are all employees background checked before hire?"),
    ("7.1", "Data", "How is our data deleted at contract termination?"),
    ("7.2", "AI", "Do you use customer data to train AI or machine learning models?"),
]


def main(out: Path = Path(__file__).with_name("sample_questionnaire.xlsx")) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Security Questionnaire"
    ws.append(["#", "Domain", "Question"])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in QUESTIONS:
        ws.append(row)
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 65
    wb.save(out)
    return out


if __name__ == "__main__":
    print(f"Wrote {main()}")
