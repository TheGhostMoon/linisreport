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
git clone [https://github.com/VOTRE_USERNAME/linisreport.git](https://github.com/VOTRE_USERNAME/linisreport.git)
cd linisreport
pip install -e .
```

## 📖 Utilisation

Lancez simplement la commande :

```bash
linisreport
```

### Raccourcis Clavier

| Touche |                Action                 |
|--------|---------------------------------------|
|`Entrer`|Ouvrir l'audit ou l'élément sélectionné|
