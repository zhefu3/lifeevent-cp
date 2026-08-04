"""Normalize raw Wikidata rows into data/processed/person_events.jsonl.

Cleaning rules (spec):
1. year cast to int (taken ONLY from the statement's own P580/P585 qualifier);
2. drop rows with missing year or missing/QID-only English target label;
3. de-duplicate on (person_id, property_id, target_id, year);
4. same-person same-year multiplicity is kept here; the question builder simply never
   hides such a year;
5/6. no year inference from any other source.
"""

from __future__ import annotations

import re
from typing import Any

from .utils import setup_logging

LOG = setup_logging()

QID_RE = re.compile(r"^Q\d+$")
# Wikidata "unknown value" statements surface as skolem genid IRIs; any URL-shaped
# label is unusable as display/model text and gets dropped (audit finding 2026-08-03).
URLISH_RE = re.compile(r"^https?://")


def _year_from_iso(value: str | None) -> int | None:
    """Extract the year from a WDQS xsd:dateTime string; None when unparseable."""
    if not value:
        return None
    m = re.match(r"^(-?\d{1,5})-", value)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def normalize_events(raw_rows: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    """Apply cleaning rules; returns normalized event rows sorted deterministically."""
    year_min, year_max = int(config["year_min"]), int(config["year_max"])
    etypes = config["event_types"]
    seen: set[tuple[str, str, str, int]] = set()
    out: list[dict[str, Any]] = []
    dropped = {"no_year": 0, "bad_label": 0, "dup": 0, "year_range": 0}

    for row in raw_rows:
        pref = etypes[row["event_type"]]["time_pref"]
        by_qualifier = {"P580": _year_from_iso(row.get("start")), "P585": _year_from_iso(row.get("point"))}
        year, time_source = None, None
        for q in pref:
            if by_qualifier.get(q) is not None:
                year, time_source = by_qualifier[q], q
                break
        if year is None:
            dropped["no_year"] += 1
            continue
        if not (year_min <= year <= year_max):
            dropped["year_range"] += 1
            continue
        target_label = (row.get("target_label") or "").strip()
        person_label = (row.get("person_label") or "").strip()
        if (not target_label or QID_RE.match(target_label) or URLISH_RE.match(target_label)
                or "genid" in target_label
                or not person_label or QID_RE.match(person_label) or URLISH_RE.match(person_label)):
            dropped["bad_label"] += 1
            continue
        key = (row["person_id"], row["property_id"], row["target_id"], year)
        if key in seen:
            dropped["dup"] += 1
            continue
        seen.add(key)
        template = etypes[row["event_type"]]["template"]
        out.append({
            "person_id": row["person_id"],
            "person_label": person_label,
            "property_id": row["property_id"],
            "event_type": row["event_type"],
            "target_id": row["target_id"],
            "target_label": target_label,
            "year": year,
            "time_source": time_source,
            "statement_uri": row.get("statement_uri", ""),
            "event_text": f"{year}: " + template.format(target=target_label),
        })

    out.sort(key=lambda r: (r["person_id"], r["year"], r["property_id"], r["target_id"]))
    LOG.info("normalize: kept %d events, dropped %s", len(out), dropped)
    return out
