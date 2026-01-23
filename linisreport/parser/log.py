# linisreport/parser/log.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import re

from ..model import (
    Finding,
    FindingType,
    guess_category,
    make_finding_id,
)

# Regex mise à jour pour gérer l'horodatage optionnel au début
_FINDING_RE = re.compile(
    r"^(?:(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+)?"
    r"(?P<prefix>\s*(?:\[\s*)?)"
    r"(?P<kind>WARNING|SUGGESTION)"
    r"(?P<mid>\s*(?:\]\s*)?(?::\s*)?)"
    r"(?P<msg>.*\S)?\s*$",
    re.IGNORECASE,
)

_INLINE_TEST_ID_RE = re.compile(r"\[test:([A-Za-z0-9_-]+)\]", re.IGNORECASE)
_CLEANUP_RE = re.compile(r"\[(details|solution):-\]\s*")


def parse_log(path: Path) -> List[Finding]:
    """
    Parse un fichier lynis.log pour extraire les warnings et suggestions.
    """
    findings: List[Finding] = []
    if not path.exists():
        return findings

    current_test_id: Optional[str] = None

    test_line_re = re.compile(r"^\s*(?:Test| Performing test ID):?\s*([A-Z0-9-]+)", re.IGNORECASE)

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            # CORRECTION ICI : On utilise enumerate(f, start=1) pour compter les lignes
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                # 1. Détection du contexte
                m_test = test_line_re.search(line)
                if m_test:
                    current_test_id = m_test.group(1).upper()
                    continue

                # 2. Détection d'un Finding
                m_find = _FINDING_RE.match(line)
                if m_find:
                    kind_str = m_find.group("kind").upper()
                    raw_msg = m_find.group("msg") or ""

                    ftype = FindingType.WARNING if kind_str == "WARNING" else FindingType.SUGGESTION

                    inline_id_match = _INLINE_TEST_ID_RE.search(raw_msg)
                    finding_test_id = current_test_id
                    
                    if inline_id_match:
                        finding_test_id = inline_id_match.group(1).upper()
                        raw_msg = raw_msg.replace(inline_id_match.group(0), "")

                    clean_msg = _CLEANUP_RE.sub("", raw_msg).strip()
                    category = guess_category(clean_msg, finding_test_id)
                    fid = make_finding_id(ftype, clean_msg, finding_test_id, category)

                    f = Finding(
                        finding_id=fid,
                        ftype=ftype,
                        message=clean_msg,
                        test_id=finding_test_id,
                        category=category,
                        evidence=[line],
                        source_file=path.name,
                        source_line_start=line_no, 
                    )
                    findings.append(f)

    except Exception as e:
        print(f"Error parsing log {path}: {e}")

    return findings