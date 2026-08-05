"""Wikidata SPARQL client with caching, retries and the two-phase fetch strategy (E-1).

Phase 1 (discovery): per (property, time-qualifier, year-slice) queries that enumerate
persons having timed statements in the slice. Slices split adaptively when they hit the
row cap or keep timing out, so no unstable LIMIT/OFFSET pagination is used.

Phase 2 (person fetch): for a selected person pool, fetch the COMPLETE set of timed
statements for every enabled property via VALUES batches, including English labels.
Downstream eligibility, distractor legality and timelines use phase-2 data only.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

from .utils import PROJECT_ROOT, setup_logging, sha1_of

LOG = setup_logging()

PREFIXES = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
PREFIX schema: <http://schema.org/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>
PREFIX hint: <http://www.bigdata.com/queryHints#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

DISCOVERY_TEMPLATE = PREFIXES + """
SELECT ?person ?t WHERE {{
  ?statement pq:{qualifier} ?t .
  hint:Prior hint:rangeSafe "true" .
  FILTER("{y0}-01-01T00:00:00Z"^^xsd:dateTime <= ?t && ?t < "{y1}-01-01T00:00:00Z"^^xsd:dateTime)
  ?person p:{prop} ?statement ;
          wdt:P31 wd:Q5 .
  ?article schema:about ?person ;
           schema:isPartOf <https://en.wikipedia.org/> .
}}
LIMIT {row_cap}
"""

PHASE2_TEMPLATE = PREFIXES + """
SELECT ?person ?personLabel ?target ?targetLabel ?start ?point ?end ?statement WHERE {{
  VALUES ?person {{ {values} }}
  ?person p:{prop} ?statement .
  ?statement ps:{prop} ?target .
  OPTIONAL {{ ?statement pq:P580 ?start . }}
  OPTIONAL {{ ?statement pq:P585 ?point . }}
  OPTIONAL {{ ?statement pq:P582 ?end . }}
  FILTER(BOUND(?start) || BOUND(?point))
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
}}
"""

# All statements of a property regardless of time qualifiers — feeds the negative-
# legality table only (TGB 2.0 lesson: an undated true statement must not become a
# "legal" negative). Never used to build questions or timelines.
ALL_TARGETS_TEMPLATE = PREFIXES + """
SELECT ?person ?target WHERE {{
  VALUES ?person {{ {values} }}
  ?person p:{prop} ?statement .
  ?statement ps:{prop} ?target .
}}
"""


class QueryTooBig(Exception):
    """Raised internally when a slice keeps timing out and should be split."""


class WikidataClient:
    """SPARQL runner: explicit UA, timeout, 429/Retry-After handling, exponential
    backoff, single-flight (concurrency 1), immediate on-disk caching."""

    def __init__(self, config: dict[str, Any], cache_dir: str | Path | None = None) -> None:
        self.config = config
        http = config["http"]
        self.timeout_s: float = float(http["timeout_s"])
        self.max_retries: int = int(http["max_retries"])
        self.backoff_base_s: float = float(http["backoff_base_s"])
        self.politeness_delay_s: float = float(http["politeness_delay_s"])
        self.endpoint: str = config["sparql_endpoint"]
        self.cache_dir = Path(cache_dir) if cache_dir else PROJECT_ROOT / config["paths"]["raw_dir"] / "sparql"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config["user_agent"], "Accept": "application/sparql-results+json"})
        self.n_network_calls = 0

    # ---------- low level ----------

    def _cache_path(self, query: str) -> Path:
        return self.cache_dir / f"{sha1_of(query)}.json"

    def run_query(self, query: str, use_cache: bool = True) -> list[dict[str, Any]]:
        """Run a SPARQL query, returning result bindings. Cached responses are reused
        by default so re-runs never re-hit the endpoint."""
        cpath = self._cache_path(query)
        if use_cache and cpath.exists():
            payload = json.loads(cpath.read_text(encoding="utf-8"))
            return payload["bindings"]

        last_err: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(self.endpoint, params={"query": query, "format": "json"},
                                        timeout=self.timeout_s)
                self.n_network_calls += 1
                if resp.status_code == 429:
                    wait = float(resp.headers.get("Retry-After", self.backoff_base_s * (2 ** attempt)))
                    LOG.warning("HTTP 429; sleeping %.1fs", wait)
                    time.sleep(wait)
                    continue
                if resp.status_code >= 500:
                    raise requests.HTTPError(f"server error {resp.status_code}")
                resp.raise_for_status()
                # strict=False: tolerate raw control characters inside labels
                bindings = resp.json(strict=False)["results"]["bindings"]
                cpath.write_text(json.dumps({"query": query, "bindings": bindings}, ensure_ascii=False),
                                 encoding="utf-8")
                time.sleep(self.politeness_delay_s)
                return bindings
            except (requests.RequestException, ValueError, KeyError) as err:
                last_err = err
                wait = self.backoff_base_s * (2 ** attempt)
                LOG.warning("query attempt %d failed (%s); backing off %.1fs", attempt + 1, err, wait)
                time.sleep(wait)
        raise QueryTooBig(f"query failed after {self.max_retries} attempts: {last_err}")

    # ---------- phase 1: discovery ----------

    def discover_slice(self, prop: str, qualifier: str, y0: int, y1: int) -> list[tuple[str, int]]:
        """(person_qid, year) rows for statements of `prop` whose `qualifier` time
        falls in [y0, y1). Splits the slice adaptively on cap/timeout."""
        row_cap = int(self.config["discovery"]["row_cap"])
        query = DISCOVERY_TEMPLATE.format(qualifier=qualifier, prop=prop, y0=y0, y1=y1, row_cap=row_cap)
        try:
            bindings = self.run_query(query)
        except QueryTooBig:
            if y1 - y0 > 1:
                mid = (y0 + y1) // 2
                LOG.info("slice %s/%s %d-%d too heavy; splitting", prop, qualifier, y0, y1)
                return self.discover_slice(prop, qualifier, y0, mid) + self.discover_slice(prop, qualifier, mid, y1)
            LOG.warning("slice %s/%s %d-%d failed at width 1; skipping", prop, qualifier, y0, y1)
            return []
        if len(bindings) >= row_cap and y1 - y0 > 1:
            mid = (y0 + y1) // 2
            LOG.info("slice %s/%s %d-%d hit row cap %d; splitting", prop, qualifier, y0, y1, row_cap)
            return self.discover_slice(prop, qualifier, y0, mid) + self.discover_slice(prop, qualifier, mid, y1)
        if len(bindings) >= row_cap:
            LOG.warning("slice %s/%s %d-%d truncated at cap %d (width 1); accepting truncation",
                        prop, qualifier, y0, y1, row_cap)
        rows: list[tuple[str, int]] = []
        for b in bindings:
            try:
                qid = b["person"]["value"].rsplit("/", 1)[-1]
                year = int(b["t"]["value"][:4])
                rows.append((qid, year))
            except (KeyError, ValueError):
                continue
        return rows

    def discover_persons(self, event_types: dict[str, dict[str, Any]], year_min: int, year_max: int) -> dict[str, dict[str, int]]:
        """Sweep all enabled (property, qualifier) pairs over [year_min, year_max]
        in adaptive slices. Returns person_qid -> {event_type: timed-event rows seen},
        so pool selection can balance across event types."""
        width = int(self.config["discovery"]["initial_slice_years"])
        counts: dict[str, dict[str, int]] = {}
        for etype, spec in sorted(event_types.items()):
            for qualifier in spec["time_pref"]:
                y = year_min
                while y <= year_max:
                    y1 = min(y + width, year_max + 1)
                    for qid, _year in self.discover_slice(spec["property"], qualifier, y, y1):
                        counts.setdefault(qid, {})[etype] = counts.get(qid, {}).get(etype, 0) + 1
                    y = y1
            LOG.info("discovery after %s: %d persons in pool", etype, len(counts))
        return counts

    # ---------- phase 2: complete person fetch ----------

    def fetch_person_events(self, person_qids: list[str], event_types: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        """Fetch ALL timed statements of every enabled property for the given persons
        (VALUES batches). Returns raw rows with labels; normalization happens later."""
        batch_size = int(self.config["phase2"]["batch_size"])
        raw_rows: list[dict[str, Any]] = []
        batches = [person_qids[i:i + batch_size] for i in range(0, len(person_qids), batch_size)]
        for bi, batch in enumerate(batches):
            values = " ".join(f"wd:{qid}" for qid in batch)
            for etype, spec in sorted(event_types.items()):
                query = PHASE2_TEMPLATE.format(values=values, prop=spec["property"])
                try:
                    bindings = self.run_query(query)
                except QueryTooBig as err:
                    LOG.warning("phase2 batch %d prop %s failed permanently: %s", bi, spec["property"], err)
                    continue
                for b in bindings:
                    raw_rows.append({
                        "person_id": b["person"]["value"].rsplit("/", 1)[-1],
                        "person_label": b.get("personLabel", {}).get("value", ""),
                        "property_id": spec["property"],
                        "event_type": etype,
                        "target_id": b["target"]["value"].rsplit("/", 1)[-1],
                        "target_label": b.get("targetLabel", {}).get("value", ""),
                        "start": b.get("start", {}).get("value"),
                        "point": b.get("point", {}).get("value"),
                        "end": b.get("end", {}).get("value"),
                        "statement_uri": b.get("statement", {}).get("value", ""),
                    })
            if (bi + 1) % 10 == 0:
                LOG.info("phase2 progress: %d/%d batches, %d raw rows", bi + 1, len(batches), len(raw_rows))
        return raw_rows

    def fetch_all_targets(self, person_qids: list[str], event_types: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
        """person_qid -> ALL target qids of enabled properties, timed or not (negative-
        legality table only)."""
        batch_size = int(self.config["phase2"]["batch_size"])
        out: dict[str, set] = {}
        batches = [person_qids[i:i + batch_size] for i in range(0, len(person_qids), batch_size)]
        for bi, batch in enumerate(batches):
            values = " ".join(f"wd:{qid}" for qid in batch)
            for _etype, spec in sorted(event_types.items()):
                query = ALL_TARGETS_TEMPLATE.format(values=values, prop=spec["property"])
                try:
                    bindings = self.run_query(query)
                except QueryTooBig as err:
                    LOG.warning("all-targets batch %d prop %s failed: %s", bi, spec["property"], err)
                    continue
                for b in bindings:
                    pid = b["person"]["value"].rsplit("/", 1)[-1]
                    out.setdefault(pid, set()).add(b["target"]["value"].rsplit("/", 1)[-1])
            if (bi + 1) % 20 == 0:
                LOG.info("all-targets progress: %d/%d batches", bi + 1, len(batches))
        return {pid: sorted(ts) for pid, ts in out.items()}
