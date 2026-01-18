# linisreport/discovery.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .model import AuditSource
# AJOUT ICI : Import du module storage
from .storage import get_snapshot_dir


@dataclass
class DiscoveryConfig:
    search_paths: List[Path] = None


DEFAULT_SEARCH_DIRS = [
    Path.home() / "lynis-audits",
    Path("/var/log"),
    get_snapshot_dir(),
]


def discover_audits(config: DiscoveryConfig = None) -> List[AuditSource]:
    """
    Scans directories for pairs of lynis.log / lynis-report.dat
    """
    cfg = config or DiscoveryConfig()
    paths = cfg.search_paths or DEFAULT_SEARCH_DIRS
    
    results = []
    seen_paths = set()

    for p in paths:
        if not p.exists():
            continue

        candidates = list(p.rglob("lynis-report.dat"))
        
        if (p / "lynis-report.dat").exists():
            candidates.append(p / "lynis-report.dat")

        for report_file in candidates:
            folder = report_file.parent
            if str(folder) in seen_paths:
                continue
            
            log_file = folder / "lynis.log"
            
            if log_file.exists() or report_file.exists():
                src = AuditSource(
                    root_dir=folder,
                    log_path=log_file if log_file.exists() else None,
                    report_path=report_file if report_file.exists() else None,
                )
                results.append(src)
                seen_paths.add(str(folder))

    return results