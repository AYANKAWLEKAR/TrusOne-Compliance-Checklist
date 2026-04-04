from pathlib import Path

import pytest

pytest.importorskip("openpyxl")

from app.ingestion.workbook import parse_checklist_workbook


def test_real_workbook_contains_expected_regulation_count() -> None:
    workbook_path = Path("/Users/ayankawlekar/Downloads/chemical_storage_compliance.xlsx")
    if not workbook_path.exists():
        return

    rows = parse_checklist_workbook(str(workbook_path))

    assert len(rows) == 37
