from app.tools.vector_search import VectorSearchTool


def test_parse_company_size_range() -> None:
    minimum, maximum = VectorSearchTool._parse_company_size("11-50")
    assert minimum == 11
    assert maximum == 50


def test_parse_company_size_open_ended() -> None:
    minimum, maximum = VectorSearchTool._parse_company_size("1000+")
    assert minimum == 1000
    assert maximum is None
