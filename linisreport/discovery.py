# linisreport/discovery.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple
import os

from .model import AuditSource


DEFAULT_SEARCH_DIRS = [
    Path("/var/log"),
    Path("/var/log/lynis-archives"),
    Path("/var/log/lynis"),
    Path("/opt/lynis-audits"),
    Path.home() / "lynis-audits",
]

# On limite la profondeur pour éviter de traverser des arbres énormes
DEFAULT_MAX_DEPTH = 4

# Fichiers attendus
LOG_NAMES = {"lynis.log"}
REPORT_NAMES = {"lynis-report.dat"}


@dataclass
class DiscoveryConfig:
    """
    Configuration de la découverte des audits.

    - search_dirs : dossiers dans lesquels on cherche des audits (par défaut des emplacements probables)
    - max_depth   : profondeur max de scan (évite /var/log/journal/... etc)
    - follow_symlinks : généralement False pour éviter les boucles
    - include_current_varlog : ajoute explicitement /var/log/lynis.{log,report} comme audit "courant"
    """
    search_dirs: List[Path] = field(default_factory=lambda: list(DEFAULT_SEARCH_DIRS))
    max_depth: int = DEFAULT_MAX_DEPTH
    follow_symlinks: bool = False
    include_current_varlog: bool = True


def discover_audits(config: Optional[DiscoveryConfig] = None) -> List[AuditSource]:
    """
    Point d'entrée principal.

    Retourne une liste d'AuditSource, triée de manière stable (par chemin).
    Le tri par date se fera plus tard, une fois qu'on aura parsé les meta (started_at / mtime).
    """
    cfg = config or DiscoveryConfig()

    sources: List[AuditSource] = []
    seen_keys: Set[str] = set()

    # 1) Ajoute l'audit "courant" si présent dans /var/log
    if cfg.include_current_varlog:
        current = _discover_current_varlog()
        if current:
            key = current.as_key()
            if key not in seen_keys:
                sources.append(current)
                seen_keys.add(key)

    # 2) Scan des dossiers probables
    for base in cfg.search_dirs:
        for src in _scan_for_audit_pairs(base, max_depth=cfg.max_depth, follow_symlinks=cfg.follow_symlinks):
            key = src.as_key()
            if key not in seen_keys:
                sources.append(src)
                seen_keys.add(key)

    # Tri stable (UI triera ensuite par date)
    sources.sort(key=lambda s: str(s.root_dir))
    return sources


def _discover_current_varlog() -> Optional[AuditSource]:
    """
    Détecte l'audit courant dans /var/log :
      /var/log/lynis.log
      /var/log/lynis-report.dat
    """
    root = Path("/var/log")
    logp = root / "lynis.log"
    repp = root / "lynis-report.dat"

    log_exists = logp.is_file()
    rep_exists = repp.is_file()

    if not log_exists and not rep_exists:
        return None

    return AuditSource(
        root_dir=root,
        log_path=logp if log_exists else None,
        report_path=repp if rep_exists else None,
    )


def _scan_for_audit_pairs(base_dir: Path, max_depth: int, follow_symlinks: bool) -> Iterable[AuditSource]:
    """
    Parcourt base_dir jusqu'à max_depth et repère des dossiers contenant
    lynis.log et/ou lynis-report.dat.

    Stratégie:
    - on visite des dossiers
    - pour chaque dossier, on regarde s'il contient un des fichiers attendus
    - si oui, on crée un AuditSource avec root_dir = dossier contenant les fichiers
    """
    base_dir = _expand_user(base_dir)

    if not base_dir.exists() or not base_dir.is_dir():
        return

    # BFS léger : file de dossiers à visiter
    queue: List[Tuple[Path, int]] = [(base_dir, 0)]
    visited: Set[Path] = set()

    while queue:
        current, depth = queue.pop(0)

        try:
            cur_resolved = current.resolve()
        except Exception:
            # Permissions / liens cassés : on ignore
            continue

        if cur_resolved in visited:
            continue
        visited.add(cur_resolved)

        # 1) Check direct dans ce dossier
        log_path = None
        report_path = None

        try:
            # listdir plutôt que glob récursif : plus rapide et contrôlé
            entries = list(current.iterdir())
        except (PermissionError, FileNotFoundError, OSError):
            continue

        for e in entries:
            if not e.is_file():
                continue
            name = e.name
            if name in LOG_NAMES:
                log_path = e
            elif name in REPORT_NAMES:
                report_path = e

        if log_path or report_path:
            yield AuditSource(root_dir=current, log_path=log_path, report_path=report_path)

        # 2) Descend si on n'a pas atteint la profondeur max
        if depth >= max_depth:
            continue

        for e in entries:
            if not e.is_dir():
                continue

            # On évite certains répertoires typiquement énormes/inutiles
            if e.name in {".git", "__pycache__", "journal"}:
                continue

            try:
                if e.is_symlink() and not follow_symlinks:
                    continue
            except OSError:
                continue

            queue.append((e, depth + 1))


def _expand_user(p: Path) -> Path:
    """
    Gère ~ proprement même si l'outil est lancé en sudo.
    """
    # Si on est en sudo, Path.home() pointe souvent vers /root.
    # Ici on respecte ce que l'utilisateur a configuré; la config par défaut utilise Path.home()
    # donc ça sera /root si sudo. C'est OK, mais on permet à l'utilisateur d'ajouter des paths.
    try:
        return p.expanduser()
    except Exception:
        return p
