# linisreport/parser/report.py
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import os
import re

from ..model import AuditMeta, AuditSource, make_audit_id


_LINE_RE = re.compile(r"^\s*([A-Za-z0-9_.:-]+)\s*=\s*(.*?)\s*$")
_QUOTED_RE = re.compile(r'^(["\'])(.*)\1$')

# Mapping des clés possibles vers nos champs AuditMeta
KEY_CANDIDATES = {
    "hostname": ["hostname", "host", "system.hostname"],
    "distro": ["os_name", "os", "distribution", "distro"],
    "distro_version": ["os_version", "os_release", "version"],
    "kernel": ["os_kernel_version_full", "os_kernel_version", "kernel_version", "uname_r"],
    "hardening_index": ["hardening_index", "compliance_score"], # Parfois absent
    "started_at": ["report_datetime_start", "scan_start", "scan.start_time"],
    "finished_at": ["report_datetime_end", "scan_end", "scan.end_time"],
}


def parse_report_dat(path: Path) -> Dict[str, Any]:
    """
    Lit un fichier clÃ©=valeur (lynis-report.dat).
    GÃ¨re les tableaux comme 'suggestion[]=...' en listes.
    """
    out = {}
    if not path.exists():
        return out

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # Gestion simple des tableaux suggestion[]=...
                is_list = False
                key_part = line.split("=", 1)[0]
                if key_part.endswith("[]"):
                    is_list = True
                    # On nettoie la clÃ© pour le regex: "suggestion[]" -> "suggestion"
                    # Mais on garde le fait que c'est une liste pour le stockage
                    clean_line = line.replace("[]=", "=", 1)
                else:
                    clean_line = line

                m = _LINE_RE.match(clean_line)
                if not m:
                    continue

                key, value = m.groups()
                key = key.lower()

                # DÃ©guillemets si nÃ©cessaire
                qm = _QUOTED_RE.match(value)
                if qm:
                    value = qm.group(2)

                if is_list:
                    # Stocker comme liste dans 'out'
                    if key not in out:
                        out[key] = []
                    # S'assurer qu'on n'Ã©crase pas une valeur prÃ©cÃ©dente qui n'Ã©tait pas liste (rare)
                    if isinstance(out[key], list):
                        out[key].append(value)
                else:
                    out[key] = value

    except Exception as e:
        print(f"Error parsing report {path}: {e}")

    return out


def extract_meta(source: AuditSource) -> AuditMeta:
    """
    Combine les infos du FS et du lynis-report.dat pour crÃ©er l'objet MÃ©ta.
    """
    data = {}
    if source.report_path:
        data = parse_report_dat(source.report_path)

    # Fonction helper pour chercher parmi les candidats
    def get_first(field_candidates: list) -> Optional[Any]:
        for k in field_candidates:
            if k in data and data[k]:
                return data[k]
        return None

    # Extraction des champs typÃ©s
    hostname = get_first(KEY_CANDIDATES["hostname"])
    distro = get_first(KEY_CANDIDATES["distro"])
    dver = get_first(KEY_CANDIDATES["distro_version"])
    kernel = get_first(KEY_CANDIDATES["kernel"])
    
    # Score (int)
    score_raw = get_first(KEY_CANDIDATES["hardening_index"])
    score = None
    if score_raw and str(score_raw).isdigit():
        score = int(score_raw)

    # Dates
    start_s = get_first(KEY_CANDIDATES["started_at"])
    end_s = get_first(KEY_CANDIDATES["finished_at"])
    
    started_at = _parse_date(start_s)
    finished_at = _parse_date(end_s)

    # ID Stable
    audit_id = make_audit_id(source.as_key(), started_at)

    return AuditMeta(
        audit_id=audit_id,
        started_at=started_at,
        finished_at=finished_at,
        hostname=hostname,
        distro=distro,
        distro_version=dver,
        kernel=kernel,
        hardening_index=score,
        source=source,
        extra=data  # On garde tout le reste pour l'affichage dÃ©taillÃ©
    )


def _parse_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    # Format lynis report: often "YYYY-MM-DD HH:MM:SS"
    # Parfois juste YYYY-MM-DD
    patterns = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for p in patterns:
        try:
            dt = datetime.strptime(s, p)
            # On suppose que c'est du local time ou UTC, on met UTC par dÃ©faut pour Ã©viter les erreurs naive/aware
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None