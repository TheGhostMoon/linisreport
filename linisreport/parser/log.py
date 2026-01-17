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
# Format supporté : "2026-01-17 20:29:38 Suggestion: ..."
_FINDING_RE = re.compile(
    r"^(?:(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+)?"  # Ignore timestamp
    r"(?P<prefix>\s*(?:\[\s*)?)"
    r"(?P<kind>WARNING|SUGGESTION)"
    r"(?P<mid>\s*(?:\]\s*)?(?::\s*)?)"
    r"(?P<msg>.*\S)?\s*$",
    re.IGNORECASE,
)

# Regex pour extraire [test:XXX] à l'intérieur du message
_INLINE_TEST_ID_RE = re.compile(r"\[test:([A-Za-z0-9_-]+)\]", re.IGNORECASE)

# Regex pour nettoyer les artefacts de fin de ligne comme [details:-] [solution:-]
_CLEANUP_RE = re.compile(r"\[(details|solution):-\]\s*")


def parse_log(path: Path) -> List[Finding]:
    """
    Parse un fichier lynis.log pour extraire les warnings et suggestions.
    """
    findings: List[Finding] = []
    if not path.exists():
        return findings

    current_test_id: Optional[str] = None

    # Regex pour détecter "Test: SSH-1234 ..." qui définit le contexte
    test_line_re = re.compile(r"^\s*(?:Test| Performing test ID):?\s*([A-Z0-9-]+)", re.IGNORECASE)

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # 1. Détection du contexte (Test ID courant)
                # Ex: "Performing test ID CORE-1000" ou "Test: SSH-7408"
                m_test = test_line_re.search(line)
                if m_test:
                    current_test_id = m_test.group(1).upper()
                    continue

                # 2. Détection d'un Finding (Warning/Suggestion)
                m_find = _FINDING_RE.match(line)
                if m_find:
                    kind_str = m_find.group("kind").upper()
                    raw_msg = m_find.group("msg") or ""

                    # Détermination du type
                    ftype = FindingType.WARNING if kind_str == "WARNING" else FindingType.SUGGESTION

                    # Extraction d'un ID inline (ex: "... [test:PHP-2372]")
                    # Cet ID est prioritaire sur le "current_test_id" du bloc
                    inline_id_match = _INLINE_TEST_ID_RE.search(raw_msg)
                    finding_test_id = current_test_id
                    
                    if inline_id_match:
                        finding_test_id = inline_id_match.group(1).upper()
                        # On retire le tag [test:...] du message pour que ce soit propre
                        raw_msg = raw_msg.replace(inline_id_match.group(0), "")

                    # Nettoyage final du message (retirer [details:-], etc.)
                    clean_msg = _CLEANUP_RE.sub("", raw_msg).strip()

                    # Deviner la catégorie
                    category = guess_category(clean_msg, finding_test_id)

                    # Création de l'ID unique
                    fid = make_finding_id(ftype, clean_msg, finding_test_id, category)

                    f = Finding(
                        finding_id=fid,
                        ftype=ftype,
                        message=clean_msg,
                        test_id=finding_test_id,
                        category=category,
                        evidence=[line], # On garde la ligne brute comme preuve
                        source_file=path.name,
                    )
                    findings.append(f)

    except Exception as e:
        print(f"Error parsing log {path}: {e}")

    return findings