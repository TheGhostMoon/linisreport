# Guide du Mainteneur - LinisReport

Ce document récapitule les processus de maintenance, de versioning et de publication pour le projet.

## 1. Gestion des Versions (SemVer)

Nous suivons le **Semantic Versioning** (`Majeure.Mineure.Correctif`).

* **X.Y.Z** (ex: `1.0.0`)
    * **X (Majeure)** : Changement cassant (ex: refonte totale, changement de config incompatible).
    * **Y (Mineure)** : Nouvelle fonctionnalité rétro-compatible (ex: ajout du mode comparaison).
    * **Z (Correctif)** : Correction de bug (ex: fix crash progressBar).

## 2. Procédure de Release (Mise en production)

Avant de publier une nouvelle version, suivre scrupuleusement ces étapes :

### Étape A : Préparation
1.  S'assurer que la branche `main` est propre et que les tests (manuels pour l'instant) passent.
2.  Mettre à jour le fichier `pyproject.toml` avec le nouveau numéro de version :
    ```toml
    version = "1.0.1"  # Exemple
    ```
3.  Mettre à jour le `CHANGELOG.md` (voir section 3) en déplaçant les éléments "Unreleased" vers la nouvelle version.

### Étape B : Git & Tagging
1.  Commiter les changements de version :
    ```bash
    git add pyproject.toml CHANGELOG.md
    git commit -m "chore(release): bump version to 1.0.1"
    ```
2.  Créer le tag Git :
    ```bash
    git tag -a v1.0.1 -m "Version 1.0.1"
    ```
3.  Pousser les modifications et le tag :
    ```bash
    git push origin main
    git push origin v1.0.1
    ```

### Étape C : GitHub Release
1.  Aller sur l'onglet **Releases** du dépôt GitHub.
2.  Cliquer sur "Draft a new release".
3.  Choisir le tag `v1.0.1`.
4.  Copier le contenu du `CHANGELOG.md` correspondant à cette version dans la description.
5.  Publier.

## 3. Nettoyage du Dépôt

* **Branches** : Une fois une fonctionnalité mergée dans `main`, supprimer la branche locale et distante :
    ```bash
    git branch -d feature/ma-super-feature
    git push origin --delete feature/ma-super-feature
    ```
* **Issues** : Fermer les issues résolues en les liant aux Pull Requests (ex: "Closes #12").