import os
import sys

import pytest


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FakeGLEIFClient:
    def search_companies(self, query: str, limit: int = 8):
        return [
            {
                "entity_id": "lei:HWUPKR0MPOU8FGXBT394",
                "name": "Apple Inc.",
                "legal_name": "Apple Inc.",
                "lei": "HWUPKR0MPOU8FGXBT394",
                "cik": None,
                "ticker": None,
                "country": "US",
                "jurisdiction": "US-CA",
                "entity_status": "ISSUED",
                "legal_form": "CORP",
                "registered_as": "C0806592",
                "legal_address": "One Apple Park Way, Cupertino, US",
                "headquarters_address": "One Apple Park Way, Cupertino, US",
                "source_labels": ["GLEIF"],
                "description": "US • ISSUED",
            }
        ]

    def get_company(self, lei: str):
        assert lei == "HWUPKR0MPOU8FGXBT394"
        return self.search_companies("Apple")[0]


class FakeSECClient:
    def search_companies(self, query: str, limit: int = 8):
        return [
            {
                "entity_id": "sec:0000320193",
                "name": "Apple Inc.",
                "legal_name": "Apple Inc.",
                "lei": None,
                "cik": "0000320193",
                "ticker": "AAPL",
                "country": None,
                "jurisdiction": None,
                "entity_status": "SEC_FILER",
                "legal_form": None,
                "registered_as": None,
                "legal_address": None,
                "headquarters_address": None,
                "source_labels": ["SEC"],
                "description": "Ticker AAPL",
            }
        ]

    def get_company_submissions(self, cik: str, limit: int = 8):
        assert cik == "0000320193"
        return {
            "entity_id": "sec:0000320193",
            "name": "Apple Inc.",
            "legal_name": "Apple Inc.",
            "lei": None,
            "cik": "0000320193",
            "ticker": "AAPL",
            "tickers": ["AAPL"],
            "country": "California",
            "jurisdiction": "CA",
            "entity_status": "operating",
            "legal_form": "Services-Computer Programming, Data Processing, Etc.",
            "registered_as": "7372",
            "legal_address": None,
            "headquarters_address": None,
            "filings": [
                {
                    "id": "0000320193-0001",
                    "form": "10-K",
                    "filing_date": "2025-11-01",
                    "accession_number": "0001",
                    "primary_document": "a10k.htm",
                }
            ],
            "source_labels": ["SEC"],
            "description": "Live disclosure metadata from SEC EDGAR",
        }


class FakeNeo4jClient:
    def __init__(self):
        self.imported_profiles = []

    def upsert_company_intelligence(self, profile):
        self.imported_profiles.append(profile)

    def load_schema(self):
        return None

    def close(self):
        return None


def test_company_search_merges_gleif_and_sec_results():
    from src.ingestion.company_intelligence import CompanyIntelligenceService

    service = CompanyIntelligenceService(gleif_client=FakeGLEIFClient(), sec_client=FakeSECClient())
    response = service.search_companies("Apple")

    assert response["count"] == 1
    assert response["source_status"]["gleif"]["live"] is True
    assert response["source_status"]["sec"]["live"] is True
    company = response["companies"][0]
    assert company["name"] == "Apple Inc."
    assert company["lei"] == "HWUPKR0MPOU8FGXBT394"
    assert company["cik"] == "0000320193"
    assert company["ticker"] == "AAPL"
    assert set(company["source_labels"]) == {"GLEIF", "SEC"}


def test_company_import_builds_live_profile_and_calls_neo4j():
    from src.ingestion.company_intelligence import CompanyIntelligenceService

    service = CompanyIntelligenceService(gleif_client=FakeGLEIFClient(), sec_client=FakeSECClient())
    neo4j = FakeNeo4jClient()

    imported = service.import_companies(
        [{"name": "Apple Inc.", "lei": "HWUPKR0MPOU8FGXBT394", "cik": "0000320193"}],
        neo4j,
    )

    assert len(imported) == 1
    assert imported[0]["company_id"] == "company:lei:HWUPKR0MPOU8FGXBT394"
    assert imported[0]["filings_imported"] == 1
    assert imported[0]["tickers"] == ["AAPL"]
    assert len(neo4j.imported_profiles) == 1
    assert neo4j.imported_profiles[0]["filings"][0]["form"] == "10-K"


def test_company_import_endpoint_uses_live_service(monkeypatch):
    import src.api.main as api_main

    fake_neo4j = FakeNeo4jClient()

    monkeypatch.setattr(api_main, "get_neo4j_client", lambda: (fake_neo4j, None))
    monkeypatch.setattr(
        api_main,
        "company_intelligence_service",
        api_main.CompanyIntelligenceService(gleif_client=FakeGLEIFClient(), sec_client=FakeSECClient()),
    )

    response = api_main.import_company_intelligence(
        api_main.CompanyImportRequest(companies=[api_main.CompanyImportSelection(name="Apple Inc.", cik="0000320193")])
    )

    assert response["source"] == "live"
    assert response["count"] == 1
    assert response["imported"][0]["name"] == "Apple Inc."


def test_bulk_company_import_collects_skipped_names():
    from src.ingestion.company_intelligence import CompanyIntelligenceService

    class EmptySECClient(FakeSECClient):
        def search_companies(self, query: str, limit: int = 8):
            if query == "Unknown Corp":
                return []
            return super().search_companies(query, limit)

        def get_company_submissions(self, cik: str, limit: int = 8):
            return super().get_company_submissions(cik, limit)

    class EmptyGLEIFClient(FakeGLEIFClient):
        def search_companies(self, query: str, limit: int = 8):
            if query == "Unknown Corp":
                return []
            return super().search_companies(query, limit)

    service = CompanyIntelligenceService(gleif_client=EmptyGLEIFClient(), sec_client=EmptySECClient())
    neo4j = FakeNeo4jClient()

    result = service.import_company_names(["Apple Inc.", "Unknown Corp"], neo4j)

    assert len(result["imported"]) == 1
    assert result["imported"][0]["name"] == "Apple Inc."
    assert result["skipped"] == [{"name": "Unknown Corp", "reason": "No live company match found"}]


def test_import_company_gracefully_falls_back_to_gleif_when_sec_enrichment_fails():
    from src.ingestion.company_intelligence import CompanyIntelligenceService

    class BrokenSECClient(FakeSECClient):
        def search_companies(self, query: str, limit: int = 8):
            raise RuntimeError("SEC unavailable")

    service = CompanyIntelligenceService(gleif_client=FakeGLEIFClient(), sec_client=BrokenSECClient())
    neo4j = FakeNeo4jClient()

    imported = service.import_companies(
        [{"name": "Apple Inc.", "lei": "HWUPKR0MPOU8FGXBT394"}],
        neo4j,
    )

    assert imported[0]["name"] == "Apple Inc."
    assert imported[0]["sources"] == ["GLEIF"]
    assert imported[0]["filings_imported"] == 0


def test_bulk_company_import_endpoint_returns_summary(monkeypatch):
    import src.api.main as api_main

    fake_neo4j = FakeNeo4jClient()

    monkeypatch.setattr(api_main, "get_neo4j_client", lambda: (fake_neo4j, None))
    monkeypatch.setattr(
        api_main,
        "company_intelligence_service",
        api_main.CompanyIntelligenceService(gleif_client=FakeGLEIFClient(), sec_client=FakeSECClient()),
    )

    response = api_main.import_company_intelligence_bulk(
        api_main.CompanyBulkImportRequest(company_names=["Apple Inc.", ""])
    )

    assert response["source"] == "live"
    assert response["count"] == 1
    assert response["skipped_count"] == 0
    assert response["imported"][0]["name"] == "Apple Inc."


def test_company_search_endpoint_rejects_empty_query():
    import src.api.main as api_main

    with pytest.raises(api_main.HTTPException) as exc_info:
        api_main.search_company_intelligence("   ")

    assert exc_info.value.status_code == 400


def test_bulk_import_request_rejects_empty_names():
    import src.api.main as api_main
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="At least one company name is required"):
        api_main.CompanyBulkImportRequest(company_names=["   ", ""])


def test_bulk_import_script_parses_newlines_and_commas():
    from scripts.import_companies import parse_company_names

    parsed = parse_company_names("Apple Inc., TSMC\nSiemens AG")
    assert parsed == ["Apple Inc.", "TSMC", "Siemens AG"]
