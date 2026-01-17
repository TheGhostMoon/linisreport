# linisreport/app.py
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import (
    Header,
    Input,
    Footer,
    Static,
    ListView,
    ListItem,
    Label,
)

from .discovery import discover_audits, DiscoveryConfig
from .loader import load_many, LoadConfig
from .model import Audit, Finding, FindingType


# -------------------------
# Small UI helpers
# -------------------------

def _fmt_dt(dt: Any) -> str:
    if not dt:
        return "unknown date"
    if isinstance(dt, str):
        return dt[:16].replace("T", " ")
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M")
    return str(dt)


def _audit_title(a: Audit) -> str:
    host = a.meta.hostname or "unknown-host"
    date = _fmt_dt(a.meta.started_at)
    score = f"{a.meta.hardening_index}" if a.meta.hardening_index is not None else "?"
    w = a.meta.warnings_count if a.meta.warnings_count is not None else len(a.warnings())
    s = a.meta.suggestions_count if a.meta.suggestions_count is not None else len(a.suggestions())
    return f"{date}  {host}  score:{score}  W:{w}  S:{s}"


def _category_stats(findings: List[Finding]) -> Tuple[int, int]:
    w = sum(1 for f in findings if f.ftype == FindingType.WARNING)
    s = sum(1 for f in findings if f.ftype == FindingType.SUGGESTION)
    return w, s


# -------------------------
# ListItem wrappers
# -------------------------

class AuditItem(ListItem):
    def __init__(self, audit: Audit) -> None:
        super().__init__(Label(_audit_title(audit)))
        self.audit = audit


class CategoryItem(ListItem):
    def __init__(self, category: str, findings: List[Finding]) -> None:
        w, s = _category_stats(findings)
        super().__init__(Label(f"{category}  (W:{w} / S:{s})"))
        self.category = category
        self.findings = findings


class FindingItem(ListItem):
    def __init__(self, finding: Finding) -> None:
        badge = "W" if finding.ftype == FindingType.WARNING else "S"
        tid = finding.test_id or finding.finding_id
        super().__init__(Label(f"[{badge}] {tid} — {finding.message}"))
        self.finding = finding


# -------------------------
# Screens
# -------------------------

class AuditListScreen(Screen):
    BINDINGS = [
        ("q", "app.quit", "Quit"),
        ("r", "reload", "Rescan"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Discovering Lynis audits…", id="status")
        yield ListView(id="audit_list")
        yield Footer()

    async def on_mount(self) -> None:
        self.run_worker(self._load_audits(), exclusive=True)

    async def _load_audits(self) -> None:
        status = self.query_one("#status", Static)
        lv = self.query_one("#audit_list", ListView)

        status.update("Scanning for audits…")
        sources = discover_audits(DiscoveryConfig())

        if not sources:
            status.update("No audits found. (Expected: /var/log/lynis.log + /var/log/lynis-report.dat, or archives.)")
            lv.clear()
            return

        status.update(f"Loading {len(sources)} audit(s)…")
        audits = load_many(sources, LoadConfig())

        def sort_key(a: Audit):
            return a.meta.started_at.timestamp() if a.meta.started_at else 0.0

        audits.sort(key=sort_key, reverse=True)

        lv.clear()
        for a in audits:
            lv.append(AuditItem(a))

        status.update("Select an audit and press Enter. (r = rescan)")
        lv.focus()

    def action_reload(self) -> None:
        self.run_worker(self._load_audits(), exclusive=True)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, AuditItem):
            self.app.push_screen(AuditHomeScreen(item.audit))


class AuditHomeScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q", "app.quit", "Quit"),
        ("p", "open_report", "Report"),
        ("x", "export_json", "Export JSON"),
    ]

    def __init__(self, audit: Audit) -> None:
        super().__init__()
        self.audit = audit

    def action_open_report(self) -> None:
        self.app.push_screen(ReportScreen(self.audit))

    def action_export_json(self) -> None:
        aid = self.audit.meta.audit_id
        filename = f"lynis_audit_{aid}.json"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.audit.to_dict(), f, indent=2)
            self.notify(f"Audit exporté : {filename}", title="Succès")
        except Exception as e:
            self.notify(f"Erreur d'export : {e}", severity="error")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        meta = self.audit.meta
        host = meta.hostname or "unknown-host"
        date = _fmt_dt(meta.started_at)
        score = f"{meta.hardening_index}" if meta.hardening_index is not None else "?"
        distro = " ".join(x for x in [meta.distro, meta.distro_version] if x) or "unknown distro"
        kernel = meta.kernel or "unknown kernel"

        yield Static(
            "\n".join(
                [
                    f"Audit: {date} — {host}",
                    f"System: {distro} | kernel: {kernel}",
                    f"Hardening index: {score} | warnings: {len(self.audit.warnings())} | suggestions: {len(self.audit.suggestions())}",
                    "",
                    "Pick a category:",
                ]
            ),
            id="audit_meta",
        )

        yield ListView(id="category_list")
        yield Footer()

    def on_mount(self) -> None:
        lv = self.query_one("#category_list", ListView)
        by_cat = self.audit.by_category()

        cats = sorted([c for c in by_cat.keys() if c != "Uncategorized"])
        if "Uncategorized" in by_cat:
            cats.append("Uncategorized")

        for c in cats:
            lv.append(CategoryItem(c, by_cat[c]))

        if lv.children:
            lv.index = 0
        lv.focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, CategoryItem):
            self.app.push_screen(FindingsScreen(self.audit, item.category, item.findings))


class FindingsScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q", "app.quit", "Quit"),
        ("w", "toggle_warnings", "Toggle Warnings"),
        ("s", "toggle_suggestions", "Toggle Suggestions"),
        ("/", "focus_search", "Search"),
    ]

    def __init__(self, audit: Audit, category: str, findings: List[Finding]) -> None:
        super().__init__()
        self.audit = audit
        self.category = category
        self._all = list(findings)
        
        self._show_warnings = True
        self._show_suggestions = True
        self._search_query = ""
        self._view = list(findings)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        w, s = _category_stats(self._all)
        yield Static(
            f"{self.category} — items:{len(self._all)} (W:{w} / S:{s})\n"
            f"[w] Toggle Warn | [s] Toggle Sugg | [/] Search",
            id="findings_title",
        )
        yield Input(placeholder="Filtrer les résultats...", id="finding_search")
        yield ListView(id="findings_list")
        yield Footer()

    def on_mount(self) -> None:
        self._update_view()
        # [FIX] On force le rendu immédiatement pour éviter la liste vide au démarrage
        self._render_list()

    def _update_view(self) -> None:
        filtered = []
        query = self._search_query.lower()
        
        for f in self._all:
            if f.ftype == FindingType.WARNING and not self._show_warnings:
                continue
            if f.ftype == FindingType.SUGGESTION and not self._show_suggestions:
                continue
            
            if query:
                blob = f"{f.message} {f.test_id or ''} {f.finding_id}".lower()
                if query not in blob:
                    continue
            
            filtered.append(f)

        self._view = filtered
        # Si on est déjà monté, on rend. Sinon on attend que on_mount le fasse.
        if self.is_mounted:
            self._render_list()

    def _render_list(self) -> None:
        lv = self.query_one("#findings_list", ListView)
        lv.clear()
        for f in self._view:
            lv.append(FindingItem(f))
        if lv.children:
            lv.index = 0

    def action_toggle_warnings(self) -> None:
        self._show_warnings = not self._show_warnings
        self.notify(f"Warnings {'ON' if self._show_warnings else 'OFF'}")
        self._update_view()

    def action_toggle_suggestions(self) -> None:
        self._show_suggestions = not self._show_suggestions
        self.notify(f"Suggestions {'ON' if self._show_suggestions else 'OFF'}")
        self._update_view()

    def action_focus_search(self) -> None:
        self.query_one("#finding_search", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "finding_search":
            self._search_query = event.value
            self._update_view()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, FindingItem):
            self.app.push_screen(FindingDetailScreen(item.finding))


class FindingDetailScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q", "app.quit", "Quit"),
    ]

    def __init__(self, finding: Finding) -> None:
        super().__init__()
        self.finding = finding

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        f = self.finding
        badge = "WARNING" if f.ftype == FindingType.WARNING else "SUGGESTION"
        tid = f.test_id or f.finding_id

        header = "\n".join(
            [
                f"{badge} — {tid}",
                f"Category: {f.category}",
                f"Message: {f.message}",
                f"Source: {f.source_file or 'unknown'}:{f.source_line_start or '?'}",
                "",
                "Evidence (log context):",
            ]
        )

        yield ScrollableContainer(
            Static(header, id="detail_header"),
            Static("\n".join(f.evidence or ["(no evidence captured)"]), id="detail_evidence"),
            id="detail_scroll",
        )

        yield Footer()


class ReportScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("q", "app.quit", "Quit"),
        ("/", "focus_search", "Search"),
        ("c", "clear_search", "Clear"),
    ]

    def __init__(self, audit: Audit) -> None:
        super().__init__()
        self.audit = audit
        self._all_lines: List[str] = []
        self._filtered_lines: List[str] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        meta = self.audit.meta
        host = meta.hostname or "unknown-host"
        date = _fmt_dt(meta.started_at)
        score = f"{meta.hardening_index}" if meta.hardening_index is not None else "?"
        distro = " ".join(x for x in [meta.distro, meta.distro_version] if x) or "unknown distro"
        kernel = meta.kernel or "unknown kernel"

        yield Static(
            "\n".join(
                [
                    f"Report viewer — {date} — {host}",
                    f"System: {distro} | kernel: {kernel}",
                    f"Hardening index: {score} | warnings: {len(self.audit.warnings())} | suggestions: {len(self.audit.suggestions())}",
                    "",
                    "Search: press / then type.  (c = clear)",
                ]
            ),
            id="report_header",
        )

        yield Input(placeholder="Filter keys/values…", id="report_search")

        yield ScrollableContainer(
            Static("", id="report_body"),
            id="report_scroll",
        )

        yield Footer()

    def on_mount(self) -> None:
        extra = self.audit.meta.extra or {}

        lines: List[str] = []
        for k in sorted(extra.keys()):
            v = extra[k]
            if isinstance(v, list):
                for idx, one in enumerate(v, start=1):
                    lines.append(f"{k}[{idx}]={one}")
            else:
                lines.append(f"{k}={v}")

        if not lines:
            lines = ["(no data found in lynis-report.dat or report was not readable)"]

        self._all_lines = lines
        self._filtered_lines = list(lines)
        self._populate_report()
        
        self.query_one("#report_search", Input).blur()
        
        # [FIX] On rend le container navigable et on lui donne le focus
        scroll = self.query_one("#report_scroll")
        scroll.can_focus = True
        scroll.focus()

    def _populate_report(self) -> None:
        body = self.query_one("#report_body", Static)
        body.update("\n".join(self._filtered_lines))

    def action_focus_search(self) -> None:
        self.query_one("#report_search", Input).focus()

    def action_clear_search(self) -> None:
        inp = self.query_one("#report_search", Input)
        inp.value = ""
        self._filtered_lines = list(self._all_lines)
        self._populate_report()
        inp.blur()
        # [FIX] Redonner le focus au scroll après avoir quitté la recherche
        self.query_one("#report_scroll").focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "report_search":
            return
        needle = event.value.strip().lower()
        if not needle:
            self._filtered_lines = list(self._all_lines)
        else:
            self._filtered_lines = [ln for ln in self._all_lines if needle in ln.lower()]
        self._populate_report()


# -------------------------
# App
# -------------------------

class LinisReportApp(App):
    CSS = """
    #status { padding: 1 2; }
    #audit_meta { padding: 1 2; }
    #findings_title { padding: 1 2; }
    #detail_scroll { padding: 1 2; }
    #detail_header { margin-bottom: 1; }
    
    /* [FIX] Style visuel pour voir que le scroll a le focus */
    #report_scroll:focus {
        border: heavy $accent;
    }
    """

    TITLE = "linisreport"
    SUB_TITLE = "Lynis audit viewer"

    def on_mount(self) -> None:
        self.push_screen(AuditListScreen())


def run() -> None:
    LinisReportApp().run()