import logging
from typing import Any, Dict, Iterable, List, Optional

from src.ingestion.gleif_client import GLEIFClient
from src.ingestion.sec_client import SECClient


logger = logging.getLogger(__name__)


class CompanyIntelligenceService:
    """Searches, enriches, and imports live company metadata from free public sources."""

    def __init__(self, gleif_client: Optional[GLEIFClient] = None, sec_client: Optional[SECClient] = None):
        self.gleif_client = gleif_client or GLEIFClient()
        self.sec_client = sec_client or SECClient()

    def search_companies(self, query: str, limit: int = 8) -> Dict[str, Any]:
        merged: Dict[str, Dict[str, Any]] = {}
        source_status = {
            "gleif": {"enabled": True, "live": False, "error": None},
            "sec": {"enabled": True, "live": False, "error": None},
        }

        try:
            for company in self.gleif_client.search_companies(query, limit=limit):
                key = self._merge_key(company)
                merged[key] = company
            source_status["gleif"]["live"] = True
        except Exception as exc:
            logger.warning("GLEIF search failed: %s", exc)
            source_status["gleif"]["error"] = str(exc)

        try:
            for company in self.sec_client.search_companies(query, limit=limit):
                key = self._find_existing_key(merged, company) or self._merge_key(company)
                existing = merged.get(key)
                merged[key] = self._merge_company(existing, company)
            source_status["sec"]["live"] = True
        except Exception as exc:
            logger.warning("SEC search failed: %s", exc)
            source_status["sec"]["error"] = str(exc)

        companies = list(merged.values())
        companies.sort(key=self._sort_key)
        return {
            "companies": companies[: max(1, min(limit, 25))],
            "count": min(len(companies), max(1, min(limit, 25))),
            "source_status": source_status,
        }

    def import_companies(self, selections: Iterable[Dict[str, Any]], neo4j_client) -> List[Dict[str, Any]]:
        imported: List[Dict[str, Any]] = []

        for selection in selections:
            if not selection.get("lei") and not selection.get("cik") and not selection.get("name"):
                raise ValueError("Each import selection must include at least a company name, LEI, or CIK")

            profile = self._hydrate_company(selection)
            neo4j_client.upsert_company_intelligence(profile)
            imported.append(
                {
                    "company_id": profile["company_id"],
                    "name": profile["name"],
                    "lei": profile.get("lei"),
                    "cik": profile.get("cik"),
                    "tickers": profile.get("tickers", []),
                    "country": profile.get("country"),
                    "filings_imported": len(profile.get("filings", [])),
                    "sources": profile.get("source_labels", []),
                }
            )

        return imported

    def import_company_names(self, company_names: Iterable[str], neo4j_client) -> Dict[str, Any]:
        imported: List[Dict[str, Any]] = []
        skipped: List[Dict[str, str]] = []

        for raw_name in company_names:
            company_name = raw_name.strip()
            if not company_name:
                continue

            try:
                search_results = self.search_companies(company_name, limit=5)
                companies = search_results["companies"]
                if not companies:
                    skipped.append({"name": company_name, "reason": "No live company match found"})
                    continue

                best_match = self._pick_best_match(company_name, companies)
                import_result = self.import_companies([best_match], neo4j_client)
                imported.extend(import_result)
            except Exception as exc:
                logger.warning("Bulk import failed for %s: %s", company_name, exc)
                skipped.append({"name": company_name, "reason": str(exc)})

        return {"imported": imported, "skipped": skipped}

    def _hydrate_company(self, selection: Dict[str, Any]) -> Dict[str, Any]:
        live_records: List[Dict[str, Any]] = []

        lei = selection.get("lei")
        cik = selection.get("cik")

        if lei:
            try:
                live_records.append(self.gleif_client.get_company(lei))
            except Exception as exc:
                logger.warning("Skipping GLEIF enrichment for %s: %s", selection.get("name") or lei, exc)

        if cik:
            try:
                live_records.append(self.sec_client.get_company_submissions(cik))
            except Exception as exc:
                logger.warning("Skipping SEC submissions enrichment for %s: %s", selection.get("name") or cik, exc)

        if not cik and selection.get("name"):
            try:
                sec_matches = self.sec_client.search_companies(selection["name"], limit=1)
                if sec_matches and self._normalize(sec_matches[0].get("name", "")) == self._normalize(selection["name"]):
                    live_records.append(self.sec_client.get_company_submissions(sec_matches[0]["cik"]))
            except Exception as exc:
                logger.warning("Skipping SEC enrichment for %s: %s", selection["name"], exc)

        if not live_records:
            live_records.append(selection)

        profile = self._merge_records(live_records)
        profile["company_id"] = self._company_id(profile)
        profile["filings"] = profile.get("filings", [])
        profile["tickers"] = list(dict.fromkeys(profile.get("tickers", []) or ([profile["ticker"]] if profile.get("ticker") else [])))
        return profile

    def _merge_records(self, records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        merged: Optional[Dict[str, Any]] = None
        for record in records:
            merged = self._merge_company(merged, record)
        if not merged:
            raise ValueError("No live company data was available to import")
        return merged

    def _merge_company(self, existing: Optional[Dict[str, Any]], incoming: Dict[str, Any]) -> Dict[str, Any]:
        if not existing:
            merged = dict(incoming)
        else:
            merged = dict(existing)
            for key, value in incoming.items():
                if key in {"source_labels", "filings", "tickers"}:
                    continue
                if value not in (None, "", []):
                    merged[key] = value

        merged_sources = list(dict.fromkeys((existing or {}).get("source_labels", []) + incoming.get("source_labels", [])))
        merged["source_labels"] = merged_sources

        merged_filing_ids = {filing["id"]: filing for filing in (existing or {}).get("filings", [])}
        for filing in incoming.get("filings", []) or []:
            merged_filing_ids[filing["id"]] = filing
        if merged_filing_ids:
            merged["filings"] = list(merged_filing_ids.values())

        tickers: List[str] = []
        for candidate in ((existing or {}).get("tickers", []), incoming.get("tickers", [])):
            for ticker in candidate or []:
                if ticker and ticker not in tickers:
                    tickers.append(ticker)
        for ticker in ((existing or {}).get("ticker"), incoming.get("ticker")):
            if ticker and ticker not in tickers:
                tickers.append(ticker)
        if tickers:
            merged["tickers"] = tickers
            merged["ticker"] = tickers[0]

        merged["entity_id"] = incoming.get("entity_id") or (existing or {}).get("entity_id")
        merged["name"] = incoming.get("name") or (existing or {}).get("name")
        merged["description"] = incoming.get("description") or (existing or {}).get("description")
        return merged

    def _find_existing_key(self, merged: Dict[str, Dict[str, Any]], company: Dict[str, Any]) -> Optional[str]:
        normalized_name = self._normalize(company.get("name", ""))
        for key, existing in merged.items():
            existing_name = self._normalize(existing.get("name", ""))
            if existing_name and normalized_name and (existing_name == normalized_name or existing_name in normalized_name or normalized_name in existing_name):
                return key
        return None

    def _merge_key(self, company: Dict[str, Any]) -> str:
        return company.get("lei") or company.get("cik") or self._normalize(company.get("name", ""))

    def _company_id(self, company: Dict[str, Any]) -> str:
        if company.get("lei"):
            return f"company:lei:{company['lei']}"
        if company.get("cik"):
            return f"company:sec:{company['cik']}"
        return f"company:name:{self._normalize(company.get('name', 'unknown-company'))}"

    def _sort_key(self, company: Dict[str, Any]) -> tuple[int, str]:
        return (-len(company.get("source_labels", [])), company.get("name", ""))

    def _pick_best_match(self, query: str, companies: List[Dict[str, Any]]) -> Dict[str, Any]:
        normalized_query = self._normalize(query)

        def score(company: Dict[str, Any]) -> tuple[int, int]:
            normalized_name = self._normalize(company.get("name", ""))
            score_value = 0
            if normalized_name == normalized_query:
                score_value += 120
            elif normalized_name.startswith(normalized_query):
                score_value += 80
            elif normalized_query in normalized_name:
                score_value += 50
            score_value += len(company.get("source_labels", [])) * 10
            return (score_value, len(company.get("source_labels", [])))

        return max(companies, key=score)

    @staticmethod
    def _normalize(value: str) -> str:
        return "".join(ch.lower() for ch in value if ch.isalnum())
