# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

## [Unreleased]

## [1.1.1] - 2026-01-23
### Fixed
- Correction du parser de logs : les numéros de ligne sont maintenant correctement extraits de `lynis.log` (ils s'affichaient sous la forme `?` auparavant).

## [1.1.0] - 2026-01-18
### Added
- **Archivage (Snapshot)** : Touche `a` pour sauvegarder un audit Live (`/var/log`) vers un dossier (`~/.local/share/linisreport/snapshots`).
- **Suppression** : Touche `d` pour supprimer une archive existante.
- **Auto-Reload** : La liste des audits se met à jour automatiquement après une suppression.
- Affichage du chemin du fichier dans la liste principale pour distinguer les doublons.
- Indicateur visuel "LIVE REPORT" vs "ARCHIVE" dans l'en-tête de l'audit.

### Changed
- Amélioration de la gestion des erreurs si un rapport est illisible (filtrage automatique).
- Le titre de l'application indique désormais le mode d'exécution (ROOT ou USER).
- Documentation mise à jour avec la méthode d'installation globale (symlink).

## [1.0.0] - 2024-01-17
### Added
- Première version stable (V1).
- Détection automatique des audits dans `/var/log` et `~/lynis-audits`.
- Interface TUI avec dashboard, liste des audits et détails.
- Filtrage des Warnings/Suggestions.
- Export JSON.
- Support du lancement via `sudo` pour les droits root.

### Fixed
- Crash de la ProgressBar lors de l'initialisation.
- Problème de focus dans l'écran de recherche.