"""
ATLAS AI — Bulk Live Company Importer

Imports a newline- or comma-separated list of company names into Neo4j using
free live sources (GLEIF + SEC EDGAR).

Usage:
  python3 scripts/import_companies.py /absolute/path/to/company_names.txt
  python3 scripts/import_companies.py --names "Apple Inc., TSMC, Siemens AG"
"""

import argparse
import csv
import os
import sys
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graph.neo4j_client import Neo4jClient
from src.ingestion.company_intelligence import CompanyIntelligenceService


def parse_company_names(raw_text: str) -> List[str]:
    return [value.strip() for value in raw_text.replace("\r", "\n").replace(",", "\n").split("\n") if value.strip()]


def load_company_names(file_path: Optional[str], raw_names: Optional[str]) -> List[str]:
    if raw_names:
        return parse_company_names(raw_names)
    if not file_path:
        raise ValueError("Provide either a file path or --names")

    with open(file_path, "r", encoding="utf-8") as handle:
        return parse_company_names(handle.read())


def load_company_rows(file_path: str) -> List[dict]:
    with open(file_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            name = (row.get("company_name") or row.get("name") or "").strip()
            if not name:
                continue
            cik = (row.get("edgar_cik") or row.get("cik") or "").strip()
            ticker = (row.get("ticker") or "").strip() or None
            country = (row.get("country") or "").strip() or None
            industry = (row.get("industry") or "").strip() or None
            sector = (row.get("sector") or "").strip() or None
            rows.append(
                {
                    "name": name,
                    "cik": cik.zfill(10) if cik else None,
                    "ticker": ticker,
                    "country": country,
                    "industry": industry,
                    "sector": sector,
                    "source_labels": ["UPLOAD"],
                    "description": "Real company metadata from uploaded CSV",
                }
            )
        return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk import live company records into Neo4j.")
    parser.add_argument("file_path", nargs="?", help="Path to a text file containing company names")
    parser.add_argument("--names", help="Comma-separated or newline-separated company names")
    parser.add_argument("--csv", action="store_true", help="Interpret the input file as a company CSV with company_name/ticker/country/edgar_cik columns")
    args = parser.parse_args()

    service = CompanyIntelligenceService()
    client = Neo4jClient()
    try:
        client.load_schema()
        if args.csv:
            if not args.file_path:
                raise SystemExit("Provide a CSV file path when using --csv")
            company_rows = load_company_rows(args.file_path)
            imported = service.import_companies(company_rows, client)
            print(f"Imported {len(imported)} companies into Neo4j.")
            for item in imported:
                tickers = ", ".join(item.get("tickers", [])) or "no ticker"
                print(f"  - {item['name']} ({tickers})")
        else:
            company_names = load_company_names(args.file_path, args.names)
            if not company_names:
                raise SystemExit("No company names were provided")
            result = service.import_company_names(company_names, client)
            print(f"Imported {len(result['imported'])} companies into Neo4j.")
            for item in result["imported"]:
                tickers = ", ".join(item.get("tickers", [])) or "no ticker"
                print(f"  - {item['name']} ({tickers})")

            if result["skipped"]:
                print(f"Skipped {len(result['skipped'])} companies:")
                for item in result["skipped"]:
                    print(f"  - {item['name']}: {item['reason']}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
