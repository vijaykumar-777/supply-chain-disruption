import logging
from typing import Any, Dict, List, Optional

import requests


logger = logging.getLogger(__name__)


class GLEIFClient:
    """Client for searching and retrieving live company records from the GLEIF API."""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.base_url = "https://api.gleif.org/api/v1/lei-records"
        self.session.headers.setdefault("Accept", "application/vnd.api+json")

    def search_companies(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        page_size = max(1, min(limit * 3, 25))
        parsed_records: Dict[str, Dict[str, Any]] = {}

        for params in (
            {"filter[entity.legalName]": query, "page[size]": page_size},
            {"filter[fulltext]": query, "page[size]": page_size},
        ):
            response = self.session.get(self.base_url, params=params, timeout=15)
            if response.status_code == 400 and "filter[entity.legalName]" in params:
                continue
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("data", []):
                parsed = self._parse_record(item)
                parsed_records[parsed["entity_id"]] = parsed

        scored: List[tuple[int, Dict[str, Any]]] = []
        for record in parsed_records.values():
            score = self._score(query, record.get("name", ""))
            if score <= 0:
                continue
            scored.append((score, record))

        scored.sort(key=lambda item: (-item[0], item[1]["name"]))
        return [item[1] for item in scored[: max(1, min(limit, 25))]]

    def get_company(self, lei: str) -> Dict[str, Any]:
        response = self.session.get(f"{self.base_url}/{lei}", timeout=15)
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data")
        if not data:
            raise ValueError(f"GLEIF returned no record for LEI {lei}")
        return self._parse_record(data)

    def _parse_record(self, item: Dict[str, Any]) -> Dict[str, Any]:
        attributes = item.get("attributes", {})
        entity = attributes.get("entity", {})
        registration = attributes.get("registration", {})
        legal_address = entity.get("legalAddress", {})
        hq_address = entity.get("headquartersAddress", {})

        legal_name = self._nested_name(entity.get("legalName"))
        name = legal_name or item.get("id") or "Unknown company"
        country = legal_address.get("country") or hq_address.get("country")
        description_parts = [part for part in [country, registration.get("status")] if part]

        return {
            "entity_id": f"lei:{item.get('id')}",
            "name": name,
            "legal_name": legal_name,
            "lei": item.get("id"),
            "cik": None,
            "ticker": None,
            "country": country,
            "jurisdiction": entity.get("jurisdiction"),
            "entity_status": registration.get("status"),
            "legal_form": entity.get("legalForm", {}).get("id"),
            "registered_as": entity.get("registeredAs"),
            "legal_address": self._format_address(legal_address),
            "headquarters_address": self._format_address(hq_address),
            "source_labels": ["GLEIF"],
            "description": " • ".join(description_parts) if description_parts else "Live company identity from GLEIF",
        }

    @staticmethod
    def _nested_name(value: Any) -> Optional[str]:
        if isinstance(value, dict):
            return value.get("name")
        return None

    @staticmethod
    def _format_address(address: Dict[str, Any]) -> Optional[str]:
        if not address:
            return None
        parts: List[str] = []
        for line in address.get("addressLines", []) or []:
            if line:
                parts.append(str(line))
        for key in ("city", "region", "postalCode", "country"):
            value = address.get(key)
            if value:
                parts.append(str(value))
        if not parts:
            return None
        return ", ".join(parts)

    @staticmethod
    def _normalize(value: str) -> str:
        return "".join(ch.lower() for ch in value if ch.isalnum())

    def _score(self, query: str, name: str) -> int:
        normalized_query = self._normalize(query)
        normalized_name = self._normalize(name)
        if not normalized_query or not normalized_name:
            return 0
        if normalized_name == normalized_query:
            return 120
        if normalized_name.startswith(normalized_query):
            return 80
        if normalized_query in normalized_name:
            return 50
        return 0
