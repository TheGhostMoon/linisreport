# linisreport/loader.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .model import Audit, AuditMeta, AuditSource, Finding, make_audit_id
from .parser.report import extract_meta
from .parser.log import parse_log


@dataclass
class LoadConfig:
    prefer_report_meta: bool = True


def load_audit(source: AuditSource, config: Optional[LoadConfig] = None) -> Audit:
    cfg = config or LoadConfig()

    meta = extract_meta(source)

    if meta.started_at is None:
        meta.started_at = _best_effort_started_at(source)
        if meta.started_at:
            meta.audit_id = make_audit_id(source.as_key(), meta.started_at)

    findings = _load_findings(source)

    audit = Audit(meta=meta, findings=findings)
    audit.recalc_counters()
    return audit


def load_many(sources: List[AuditSource], config: Optional[LoadConfig] = None) -> List[Audit]:
    """
    Charge les audits et filtre ceux qui sont illisibles ou vides.
    """
    cfg = config or LoadConfig()
    results = []
    
    for s in sources:
        audit = load_audit(s, cfg)
        
        is_empty = (
            audit.meta.hardening_index is None 
            and not audit.findings
            and not audit.meta.hostname
        )
        
        if not is_empty:
            results.append(audit)
            
    return results


def _load_findings(source: AuditSource) -> List[Finding]:
    log_path = source.log_path
    if not log_path or not log_path.is_file():
        return []
    
    return parse_log(log_path)


def _best_effort_started_at(source: AuditSource) -> Optional[datetime]:
    candidates: List[Path] = []
    if source.report_path and source.report_path.exists():
        candidates.append(source.report_path)
    if source.log_path and source.log_path.exists():
        candidates.append(source.log_path)

    best_ts: Optional[float] = None
    for p in candidates:
        try:
            ts = p.stat().st_mtime
            if best_ts is None or ts > best_ts:
                best_ts = ts
        except Exception:
            continue

    if best_ts is None:
        return None
    return datetime.fromtimestamp(best_ts, tz=timezone.utc)