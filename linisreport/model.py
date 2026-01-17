# linisreport/model.py
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import re
from datetime import datetime, timezone


class FindingType(str, Enum):
    WARNING = "warning"
    SUGGESTION = "suggestion"


@dataclass(frozen=True)
class AuditSource:
    """
    Where an audit was loaded from on disk.
    """
    root_dir: Path
    log_path: Optional[Path] = None
    report_path: Optional[Path] = None

    def is_complete(self) -> bool:
        return bool(self.log_path and self.report_path)

    def as_key(self) -> str:
        # Stable key used for caching/indexing
        parts = [
            str(self.root_dir.resolve()),
            str(self.log_path.resolve()) if self.log_path else "",
            str(self.report_path.resolve()) if self.report_path else "",
        ]
        return "|".join(parts)


@dataclass
class AuditMeta:
    """
    Metadata extracted from lynis-report.dat and/or inferred from filesystem.
    """
    # identity
    audit_id: str

    # timing
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    # system
    hostname: Optional[str] = None
    distro: Optional[str] = None
    distro_version: Optional[str] = None
    kernel: Optional[str] = None

    # scoring & counters
    hardening_index: Optional[int] = None
    warnings_count: Optional[int] = None
    suggestions_count: Optional[int] = None

    # paths / provenance
    source: Optional[AuditSource] = None

    # free-form (keep everything else we parse)
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Finding:
    """
    One WARNING or SUGGESTION with optional test id and evidence snippets.
    """
    finding_id: str                      # stable identifier (test_id if available, else generated)
    ftype: FindingType                   # warning/suggestion
    message: str                         # human-facing text (short/medium)
    test_id: Optional[str] = None        # e.g. SSH-7408
    category: str = "Uncategorized"      # e.g. SSH, Firewall, Kernel...
    details: List[str] = field(default_factory=list)    # more text (if present)
    evidence: List[str] = field(default_factory=list)   # extracted log lines, short
    references: List[str] = field(default_factory=list) # URLs/refs if we detect them

    # Where it came from (useful when debugging)
    source_file: Optional[str] = None
    source_line_start: Optional[int] = None

    # Comparison helpers (set later by compare mode)
    status: str = "unchanged"  # "new" | "resolved" | "unchanged"

    def normalized_fingerprint(self) -> str:
        """
        Used when test_id is missing to compare across audits.
        """
        base = f"{self.ftype.value}|{self.category}|{normalize_text(self.message)}"
        if self.test_id:
            base = f"{base}|{self.test_id}"
        return sha1_hex(base)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["ftype"] = self.ftype.value
        return d


@dataclass
class Audit:
    meta: AuditMeta
    findings: List[Finding] = field(default_factory=list)

    def warnings(self) -> List[Finding]:
        return [f for f in self.findings if f.ftype == FindingType.WARNING]

    def suggestions(self) -> List[Finding]:
        return [f for f in self.findings if f.ftype == FindingType.SUGGESTION]

    def by_category(self) -> Dict[str, List[Finding]]:
        out: Dict[str, List[Finding]] = {}
        for f in self.findings:
            out.setdefault(f.category or "Uncategorized", []).append(f)
        return out

    def recalc_counters(self) -> None:
        self.meta.warnings_count = len(self.warnings())
        self.meta.suggestions_count = len(self.suggestions())

    def to_dict(self) -> Dict[str, Any]:
        meta = asdict(self.meta)
        if self.meta.source:
            meta["source"] = {
                "root_dir": str(self.meta.source.root_dir),
                "log_path": str(self.meta.source.log_path) if self.meta.source.log_path else None,
                "report_path": str(self.meta.source.report_path) if self.meta.source.report_path else None,
                "complete": self.meta.source.is_complete(),
                "key": self.meta.source.as_key(),
            }
        # datetimes -> iso
        for k in ("started_at", "finished_at"):
            if meta.get(k) is not None:
                meta[k] = meta[k].astimezone(timezone.utc).isoformat()

        return {
            "meta": meta,
            "findings": [f.to_dict() for f in self.findings],
        }


# ----------------------------
# Helpers / normalization
# ----------------------------

_WS_RE = re.compile(r"\s+")
_NONPRINT_RE = re.compile(r"[^\x09\x0A\x0D\x20-\x7E]+")


def normalize_text(s: str) -> str:
    """
    Normalizes a text to improve stable hashing/comparison:
    - remove non-printable
    - collapse whitespace
    - strip
    - lowercase
    """
    if s is None:
        return ""
    s = _NONPRINT_RE.sub("", s)
    s = _WS_RE.sub(" ", s).strip().lower()
    return s


def sha1_hex(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="replace")).hexdigest()


def make_audit_id(source_key: str, started_at: Optional[datetime] = None) -> str:
    """
    Creates a stable audit id. If started_at exists, include it (keeps IDs stable and human-friendly).
    """
    if started_at:
        ts = started_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        base = f"{source_key}|{ts}"
    else:
        base = source_key
    return sha1_hex(base)[:16]


def make_finding_id(
    ftype: FindingType,
    message: str,
    test_id: Optional[str] = None,
    category: Optional[str] = None,
) -> str:
    """
    Preferred: test_id if present (unique enough for Lynis).
    Else: stable short hash from normalized fields.
    """
    if test_id:
        return test_id.strip()
    base = f"{ftype.value}|{category or ''}|{normalize_text(message)}"
    return sha1_hex(base)[:12]


# ----------------------------
# Category heuristics (lightweight)
# ----------------------------

CATEGORY_RULES: List[Tuple[str, List[str]]] = [
    ("SSH", ["ssh", "sshd", "openssh"]),
    ("Firewall", ["ufw", "iptables", "nftables", "firewalld", "pf"]),
    ("Auth/PAM", ["pam", "sudo", "passwd", "shadow", "auth", "login"]),
    ("Kernel", ["sysctl", "kernel", "grub", "aslr", "modules", "spectre", "mitigation"]),
    ("Services", ["systemd", "service", "daemon", "listening", "port", "rpc"]),
    ("Logging/Auditing", ["rsyslog", "journald", "logrotate", "auditd", "syslog"]),
    ("Updates/Packages", ["apt", "dnf", "yum", "updates", "upgrade", "package"]),
    ("Crypto/TLS", ["tls", "ssl", "openssl", "cipher", "certificate"]),
    ("Filesystems/Permissions", ["permission", "permissions", "umask", "mount", "fstab", "sticky", "suid", "sgid"]),
    ("Network", ["ipv4", "ipv6", "tcp", "udp", "icmp", "net", "dns"]),
]


def guess_category(message: str, test_id: Optional[str] = None) -> str:
    """
    Simple heuristic classifier: keywords first, then test_id prefixes if you add later.
    Keep it conservative and predictable.
    """
    hay = normalize_text(f"{test_id or ''} {message}")
    for cat, keys in CATEGORY_RULES:
        for k in keys:
            if k in hay:
                return cat
    return "Uncategorized"


def compare_audits(old: Audit, new: Audit) -> Dict[str, List[Finding]]:
    """
    Compare deux audits et retourne les findings classés par état:
    - new: présent dans 'new' mais pas dans 'old'
    - resolved: présent dans 'old' mais pas dans 'new'
    - persistent: présent dans les deux
    """
    # Création de map basées sur le fingerprint (stable)
    old_map = {f.normalized_fingerprint(): f for f in old.findings}
    new_map = {f.normalized_fingerprint(): f for f in new.findings}
    
    res = {
        "new": [],
        "resolved": [],
        "persistent": []
    }
    
    for fp, f in new_map.items():
        if fp in old_map:
            f.status = "unchanged"
            res["persistent"].append(f)
        else:
            f.status = "new"
            res["new"].append(f)
            
    for fp, f in old_map.items():
        if fp not in new_map:
            f.status = "resolved"
            res["resolved"].append(f)
            
    return res