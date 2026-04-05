import pytest

from app.config import _validate_database_url_template


def test_validate_database_url_template_rejects_placeholder_values() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL still contains template placeholders"):
        _validate_database_url_template(
            "postgresql://postgres:<password>@db.<project-ref>.supabase.co:6543/postgres"
        )


def test_validate_database_url_template_accepts_real_values() -> None:
    assert (
        _validate_database_url_template(
            "postgresql://postgres:secret@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
        )
        == "postgresql://postgres:secret@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    )
