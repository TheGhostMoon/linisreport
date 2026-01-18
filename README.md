# LinisReport

Une interface terminal moderne (TUI) pour analyser, filtrer et explorer les rapports d'audit de sécurité **Lynis**.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Textual](https://img.shields.io/badge/Built%20with-Textual-purple)

LinisReport transforme les fichiers logs bruts de Lynis (`lynis.log` et `lynis-report.dat`) en un tableau de bord interactif, permettant de naviguer facilement dans les avertissements et suggestions de sécurité.

## 🚀 Fonctionnalités

* **Auto-découverte** : Détecte automatiquement les audits présents dans `~/lynis-audits` ou `/var/log`.
* **Tableau de bord** : Vue synthétique avec score de durcissement (hardening index), OS, kernel et statistiques.
* **Navigation par catégorie** : Explorez les résultats groupés (SSH, Firewall, Kernel, etc.).
* **Filtrage puissant** : 
    * Recherche textuelle instantanée.
    * Afficher/Masquer les *Warnings* ou *Suggestions*.
* **Détails complets** : Visualisez les preuves (evidence) et le contexte technique de chaque alerte.
* **Inspecteur de rapport** : Vue brute des métadonnées (clés/valeurs) avec recherche.
* **Export JSON** : Exportez l'audit en format JSON structuré pour une utilisation externe.

## 🛠️ Installation

### Prérequis
* Python 3.10 ou supérieur.
* Un système Linux/macOS (pour l'affichage correct du terminal).

### Installation (Développement)

Clonez ce dépôt et installez-le en mode éditable :

```bash
git clone https://github.com/TheGhostMoon/linisreport.git
cd linisreport
pip install -e .
```

## 📖 Utilisation

### Mode automatique (Recommandé)

Par défaut, Lynis sauvegarde ses rapports (`lynis.log` et `lynis-report.dat`) dans `/var/log/`. Ces fichiers sont protégés et appartiennent à l'utilisateur `root`.

Pour que **LinisReport** détecte et lise automatiquement ces fichiers sans aucune configuration manuelle, lancez-le avec `sudo` :

```bash
# Si installé globalement
sudo linisreport

# Si installé dans un environnement virtuel (venv)
sudo ./.venv/bin/linisreport
```

L'outil scannera automatiquement `/var/log` et affichera votre dernier audit.

### Mode fichier (Sans root)
Si vous ne souhaitez pas lancer l'outil en root ou si vous analysez des rapports récupérés d'une autre machine, placez simplement les fichiers dans un dossier local (ex: `~/lynis-audits/`) et lancez l'outil normalement.

### Raccourcis Clavier

| Touche   | Action                                             |
|----------|----------------------------------------------------|
| `Entrer` | Ouvrir l'audit ou l'élément sélectionné            |
| `Esc`    | Retour à l'écran précédent                         |
| `/`      | Rechercher (dans les listes ou le rapport)         |
| `w`      | Afficher/Masquer les Warnings                      |
| `s`      | Afficher/Masquer les Suggestions                   |
| `p`      | Ouvrir les détails bruts du rapport (Report Viewer)|
| `x`      | Exporter l'audit courant en JSON                   |
| `q`      | Quitter l'application                              |

## 🏗️ Architecture

Le projet est construit avec Textual (Python TUI framework) et structuré comme suit :
 - `app.py` : Gestion de l'interface (Screens, Widgets).
 - `model.py` : Structures de données (Dataclasses).
 - `parser/` : Logique d'extraction des fichiers Lynis.
 - `discovery.py` : Recherche des fichiers sur le disque.

## 🤝 Contribuer

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une "Issue" ou à proposer une "Pull Request".
 1. Forkez le projet.
 2. Créez votre branche (`git checkout -b feature/AmazingFeature`).
 3. Commitez vos changements (`git commit -m 'Add some AmazingFeature`).
 4. Pushez sur la branche (`git push origin feature/AmazingFeature`).
 5. Ouvrez une Pull Request.

## 📄 Licence

Distribué sous la licence MIT. Voir `LICENSE` pour plus d'information
