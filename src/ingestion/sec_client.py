import logging
import time
from typing import Any, Dict, List, Optional

import requests

from src.config import SEC_API_USER_AGENT


logger = logging.getLogger(__name__)


class SECClient:
    """Client for public-company metadata and filing data from the SEC."""

    _ticker_cache: Dict[str, Any] = {"loaded_at": 0.0, "records": []}
    _ticker_cache_ttl = 60 * 60 * 12

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", SEC_API_USER_AGENT)
        self.session.headers.setdefault("Accept", "application/json")
        self.tickers_url = "https://www.sec.gov/files/company_tickers.json"
        self.submissions_url = "https://data.sec.gov/submissions/CIK{cik}.json"

    def search_companies(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        normalized_query = self._normalize(query)
        if not normalized_query:
            return []

        records = self._load_ticker_records()
        ranked: List[tuple[int, Dict[str, Any]]] = []

        for record in records:
            title = record.get("title", "")
            ticker = record.get("ticker", "")
            title_norm = self._normalize(title)
            ticker_norm = self._normalize(ticker)
            score = self._score(normalized_query, title_norm, ticker_norm)
            if score <= 0:
                continue

            ranked.append(
                (
                    score,
                    {
                        "entity_id": f"sec:{self._pad_cik(record.get('cik_str'))}",
                        "name": title,
                        "legal_name": title,
                        "lei": None,
                        "cik": self._pad_cik(record.get("cik_str")),
                        "ticker": ticker or None,
                        "country": None,
                        "jurisdiction": None,
                        "entity_status": "SEC_FILER",
                        "legal_form": None,
                        "registered_as": None,
                        "legal_address": None,
                        "headquarters_address": None,
                        "source_labels": ["SEC"],
                        "description": f"Ticker {ticker}" if ticker else "Live public company record from SEC",
                    },
                )
            )

        ranked.sort(key=lambda item: (-item[0], item[1]["name"]))
        return [item[1] for item in ranked[: max(1, min(limit, 25))]]

    def get_company_submissions(self, cik: str, limit: int = 8) -> Dict[str, Any]:
        padded_cik = self._pad_cik(cik)
        response = self.session.get(self.submissions_url.format(cik=padded_cik), timeout=20)
        response.raise_for_status()
        payload = response.json()

        tickers = payload.get("tickers") or []
        recent = payload.get("filings", {}).get("recent", {})
        forms = recent.get("form", []) or []
        filing_dates = recent.get("filingDate", []) or []
        accession_numbers = recent.get("accessionNumber", []) or []
        primary_documents = recent.get("primaryDocument", []) or []

        filings: List[Dict[str, Any]] = []
        for index, form in enumerate(forms[: max(1, min(limit, 20))]):
            accession_number = accession_numbers[index] if index < len(accession_numbers) else None
            filing_id = f"{padded_cik}-{accession_number}" if accession_number else f"{padded_cik}-{index}"
            filings.append(
                {
                    "id": filing_id,
                    "form": form,
                    "filing_date": filing_dates[index] if index < len(filing_dates) else None,
                    "accession_number": accession_number,
                    "primary_document": primary_documents[index] if index < len(primary_documents) else None,
                }
            )

        return {
            "entity_id": f"sec:{padded_cik}",
            "name": payload.get("name") or padded_cik,
            "legal_name": payload.get("name") or padded_cik,
            "lei": None,
            "cik": padded_cik,
            "ticker": tickers[0] if tickers else None,
            "tickers": tickers,
            "country": payload.get("stateOfIncorporationDescription"),
            "jurisdiction": payload.get("stateOfIncorporation"),
            "entity_status": payload.get("entityType") or "SEC_FILER",
            "legal_form": payload.get("sicDescription"),
            "registered_as": payload.get("sic"),
            "legal_address": None,
            "headquarters_address": None,
            "filings": filings,
            "source_labels": ["SEC"],
            "description": "Live disclosure metadata from SEC EDGAR",
        }

    def _load_ticker_records(self) -> List[Dict[str, Any]]:
        now = time.time()
        if now - self._ticker_cache["loaded_at"] < self._ticker_cache_ttl and self._ticker_cache["records"]:
            return self._ticker_cache["records"]

        response = self.session.get(self.tickers_url, timeout=20)
        response.raise_for_status()
        payload = response.json()

        if isinstance(payload, dict):
            if all(isinstance(value, dict) for value in payload.values()):
                records = list(payload.values())
            else:
                records = payload.get("data", [])
        elif isinstance(payload, list):
            records = payload
        else:
            records = []

        self._ticker_cache = {"loaded_at": now, "records": records}
        return records

    @staticmethod
    def _pad_cik(value: Any) -> str:
        return str(value).strip().zfill(10)

    @staticmethod
    def _normalize(value: str) -> str:
        return "".join(ch.lower() for ch in value if ch.isalnum())

    def _score(self, query: str, title: str, ticker: str) -> int:
        score = 0
        if ticker == query:
            score += 120
        elif ticker.startswith(query):
            score += 80
        elif query in ticker:
            score += 60

        if title == query:
            score += 100
        elif title.startswith(query):
            score += 70
        elif query in title:
            score += 45

        return score
