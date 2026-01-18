# Contribuer à LinisReport

Merci de vouloir contribuer à ce projet ! Voici quelques règles simples pour garder le code propre et l'historique lisible.

## 🛠️ Installation pour le développement

1.  Cloner le dépôt.
2.  Créer un environnement virtuel :
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3.  Installer le projet en mode éditable :
    ```bash
    pip install -e .
    ```

## 🎨 Style de Code

* **Framework** : Le projet utilise [Textual](https://textual.textualize.io/).
* **Typage** : Utilisez le *Type Hinting* de Python partout (ex: `def func(a: int) -> str:`).
* **Structure** :
    * `app.py` : Uniquement la logique d'interface (Widgets, Screens).
    * `model.py` : Uniquement les données (Dataclasses, logique métier).
    * `parser/` : Uniquement le parsing de fichiers textes.

## 🌳 Gestion des branches

Ne travaillez jamais directement sur `main`.
* Créez une branche pour chaque tâche :
    * `feat/nom-de-la-feature` (pour une nouveauté)
    * `fix/nom-du-bug` (pour une correction)
    * `docs/ajout-readme` (pour de la documentation)

## 📝 Messages de Commit (Convention)

Nous suivons la convention **Conventional Commits** pour garder un historique clair.
Format : `type(portée): description courte`

Types autorisés :
* **feat** : Une nouvelle fonctionnalité (augmente la version Mineure).
* **fix** : Correction de bug (augmente la version Correctif).
* **docs** : Changement dans la documentation uniquement.
* **style** : Formatage, point-virgule manquant, etc. (pas de changement de code).
* **refactor** : Refactorisation du code sans changer le comportement.
* **chore** : Tâches de maintenance (ex: mise à jour de version, .gitignore).

**Exemples :**
* `feat(ui): add progress bar for hardening score`
* `fix(parser): ignore timestamp in log lines`
* `docs(readme): add sudo usage instructions`

## 🚀 Soumettre une Pull Request (PR)

1.  Assurez-vous que votre code fonctionne.
2.  Poussez votre branche sur GitHub.
3.  Ouvrez une PR vers `main`.
4.  Décrivez clairement ce que fait votre PR et pourquoi.