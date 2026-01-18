# linisreport/storage.py
from __future__ import annotations

import shutil
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from .model import Audit

# Dossier standard XDG pour les données utilisateur
SNAPSHOT_ROOT = Path.home() / ".local" / "share" / "linisreport" / "snapshots"

def get_snapshot_dir() -> Path:
    """Retourne le dossier racine des snapshots (le crée si besoin)."""
    SNAPSHOT_ROOT.mkdir(parents=True, exist_ok=True)
    return SNAPSHOT_ROOT

def is_stored_snapshot(audit: Audit) -> bool:
    """
    Vérifie si l'audit est stocké dans le dossier des snapshots.
    Permet de distinguer un audit 'Live' d'une archive.
    """
    if not audit.meta.source or not audit.meta.source.root_dir:
        return False
    try:
        # On compare les chemins absolus pour être sûr
        # On vérifie si le dossier de l'audit est un enfant de SNAPSHOT_ROOT
        audit_path = audit.meta.source.root_dir.resolve()
        root_path = get_snapshot_dir().resolve()
        return root_path in audit_path.parents
    except Exception:
        return False

def create_snapshot(audit: Audit) -> Path:
    """
    Copie les fichiers de l'audit vers un dossier basé sur la date du scan.
    """
    root = get_snapshot_dir()
    source = audit.meta.source

    if not source:
        raise ValueError("Impossible d'archiver : source inconnue.")

    # Vérification : on n'archive pas une archive
    if is_stored_snapshot(audit):
         raise ValueError("Cet audit est déjà une archive.")

    # Génération du nom basé sur la date de l'AUDIT
    ts_date = audit.meta.started_at or datetime.now()
    ts_str = ts_date.strftime("%Y-%m-%d_%H%M%S")
    host = audit.meta.hostname or "unknown"
    folder_name = f"{ts_str}_{host}"
    
    dest_dir = root / folder_name
    
    if dest_dir.exists():
        raise FileExistsError(f"L'archive existe déjà : {folder_name}")
    
    dest_dir.mkdir(exist_ok=True)

    files_copied = 0
    if source.log_path and source.log_path.exists():
        shutil.copy2(source.log_path, dest_dir / "lynis.log")
        files_copied += 1
        
    if source.report_path and source.report_path.exists():
        shutil.copy2(source.report_path, dest_dir / "lynis-report.dat")
        files_copied += 1
        
    if files_copied == 0:
        shutil.rmtree(dest_dir)
        raise ValueError("Aucun fichier source n'a pu être copié.")
        
    return dest_dir

def delete_snapshot(audit: Audit) -> None:
    """
    Supprime le dossier de l'audit UNIQUEMENT si c'est une archive gérée par nous.
    """
    if not is_stored_snapshot(audit):
        raise ValueError("Sécurité : Impossible de supprimer un audit qui n'est pas dans le dossier d'archives.")
    
    if audit.meta.source and audit.meta.source.root_dir:
        shutil.rmtree(audit.meta.source.root_dir)