# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

## [Unreleased]
*Ici, on note ce qu'on fait en attendant la prochaine version.*

## [1.0.0] - 2024-XX-XX
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