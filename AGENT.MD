# AGENT.MD

## 1. Vue d’ensemble du projet

- **Objectif** : afficher en temps réel les tirs sur des cibles (target display). Le serveur reçoit des données brutes sur un socket TCP, les persiste dans une base MariaDB et expose une API REST pour la vue web.
- **Stack technique** :
  - Langage principal : **Python 3.11** (Flask 2.x)
  - Base de données : **MariaDB** (access via `mariadb` package)
  - Front‑end : HTML + SVG + vanilla JavaScript (no framework)
  - Configuration : variables d’environnement via `python‑dotenv`.
  - Gestion de dépendances : `requirements.txt`.

## 2. Architecture et structure du projet

```
polytronic-target-display/               # racine
├─ app.py                 # point d’entrée Flask + thread TCP
├─ app_api.py             # Blueprint API (shots endpoint)
├─ app_routes.py          # Blueprint routes (HTML pages)
├─ database/
│  ├─ receiver.py         # TCP listener + parser
│  ├─ database_rw.py      # CRUD vers MariaDB
│  ├─ create_structure.sql
│  └─ __init__.py
├─ static/
│  ├─ style.css
│  ├─ fullscreen.css
│  ├─ favicon.ico
│  └─ js/update-target.js
├─ templates/
│  ├─ home.html
│  ├─ target.html
│  ├─ target_fs.html
│  ├─ credits.html
│  └─ test.html
├─ requirements.txt
├─ .gitignore
├─ README.md
└─ AGENT.MD                # this file
```

**Interactions principales**

- `app.py` démarre le serveur Flask _et_ le thread `listen()` de `database.receiver`.
- `database.receiver` écoute sur le port défini par `PORT_LISTENER`, parse chaque ligne et appelle les méthodes de `InitTarget` (stockées dans la liste `targets`).
- `database.database_rw.InitTarget` écrit dans les tables `programm`, `series`, `shots`.
- `app_api.get_shots` lit les tirs d’une cible via `database_rw.readShot` et renvoie un JSON consommé par `static/js/update-target.js`.
- Le front‑end actualise les SVG toutes les 2 s.

## 3.1. Améliorations récentes

- **`listLastShot`** : ajout d’un en‑tête détaillé (description, paramètres, type de retour, notes) pour clarifier son usage.
- **`get_data`** : simplification de la gestion des ressources grâce à un seul bloc `with` contenant la connexion et le curseur. La logique de détection du SELECT repose désormais sur `cursor.description` (au lieu de l’attribut interne `cursor._text`).
- **Images de cible** : les balises `<image>` dans `templates/target.html` et `templates/target_fs.html` pointent maintenant vers `/static/assets/{{ target_type }}.png` via le script JavaScript, permettant un changement d’image dynamique.
- **`update-target.js`** : après mise à jour de l’image, la fonction `drawShotsOnSvg` est appelée pour dessiner les tirs, garantissant que l’affichage reste synchronisé avec l’image.
- **`writer.py`** :
  - Docstring de la fonction interne `doWriteQuery` traduite en anglais.
  - Commentaires internes (lignes 8‑9 et 13‑13) traduits en anglais pour la cohérence.
  - Le `fetchone()` est appelé avant le `commit()`, ce qui fonctionne correctement car `LAST_INSERT_ID()` reste disponible jusqu’à la prochaine requête `INSERT`.

## 3. Conventions de code et règles

| Domaine                 | Conventions                                                                                                                                                                                                                                                                  |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Python**              | `snake_case` pour fonctions, variables, modules. Docstrings PEP‑257 + type hints. Utilisation de `print` pour les logs (pas de `logging`). Gestion des erreurs avec `try/except` et `print` d’erreurs. Les connexions DB sont créées à chaque appel via `_get_connection()`. |
| **JavaScript**          | `camelCase` pour fonctions et variables. Fichiers `.js` sans framework. Utilisation d’`async/await` pour les fetch.                                                                                                                                                          |
| **Configuration**       | Variables d’environnement chargées par `python-dotenv`. Fichier `.env.example` fourni.                                                                                                                                                                                       |
| **SQL**                 | Tables créées par `create_structure.sql`. Noms en minuscules, `snake_case`.                                                                                                                                                                                                  |
| **Structure du projet** | Root-level scripts (`app.py`) et packages (`database`). Les templates sont sous `templates/`. Les assets statiques sous `static/`.                                                                                                                                           |
| Domaine                 | Conventions                                                                                                                                                                                                                                                                  |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Python**              | `snake_case` pour fonctions, variables, modules. Docstrings PEP‑257 + type hints. Utilisation de `print` pour les logs (pas de `logging`). Gestion des erreurs avec `try/except` et `print` d’erreurs. Les connexions DB sont créées à chaque appel via `_get_connection()`. |
| **JavaScript**          | `camelCase` pour fonctions et variables. Fichiers `.js` sans framework. Utilisation d’`async/await` pour les fetch.                                                                                                                                                          |
| **Configuration**       | Variables d’environnement chargées par `python-dotenv`. Fichier `.env.example` fourni.                                                                                                                                                                                       |
| **SQL**                 | Tables créées par `create_structure.sql`. Noms en minuscules, `snake_case`.                                                                                                                                                                                                  |
| **Structure du projet** | Root-level scripts (`app.py`) et packages (`database`). Les templates sont sous `templates/`. Les assets statiques sous `static/`.                                                                                                                                           |

**Gestion des erreurs**

- La couche TCP ne traite pas les erreurs de format ; elle ignore les lignes vides ou mal formées.
- Les interactions DB enveloppent chaque requête dans `try/except` et rollback en cas d’erreur.
- L’API renvoie 400 si le paramètre `target` manque.

## 4. État d’avancement et roadmap

| État           | Détails                                                                    |
| -------------- | -------------------------------------------------------------------------- |
| **Implémenté** | • Listener TCP + parsing (receiver.py)                                     |
|                | • Modèle de données MariaDB et fonctions CRUD (database_rw.py)             |
|                | • API `/api/shots` (app_api.py)                                            |
|                | • Vue front‑end avec SVG et rafraîchissement (update-target.js, templates) |
|                | • Démarrage serveur Flask + thread TCP (app.py)                            |
|                | • README + requirements                                                    |
| **À faire**    | • Ajouter des tests unitaires (pytest) pour la couche DB et API.           |
|                | • Améliorer le logging (passer à `logging`).                               |
|                | • Gestion des erreurs plus robuste (validation des données reçues).        |
|                | • Documentation détaillée (docs/).                                         |
|                | • Authentification pour l’API (token ou JWT).                              |
|                | • Optimiser les requêtes SQL (index, caching).                             |
|                | • Déployer sur un serveur (Dockerfile).                                    |

## 5. Directives pour l’Agent IA

1. **Priorité de lecture** :
   - `app.py` – compréhension du bootstrap.
   - `database/receiver.py` – parsing de données TCP.
   - `database/database_rw.py` – logique DB, `InitTarget`.
   - `app_api.py` – API REST.
   - `static/js/update-target.js` – logique front‑end.
   - `templates/` – structure HTML.
2. **Réponses** :
   - Répondre en code complet lorsqu’une modification est requise.
   - Utiliser le format Markdown pour les explications.
   - Mentionner les fichiers modifiés et la raison de la modification.
3. **Considérations** :
   - Toujours garder le style existant (snake_case, docstrings).
   - Éviter de modifier des dépendances externes sans raison.
   - Tester les changements localement (exécution de `app.py` ou appel d’API) avant de proposer le patch.

---

_Ce fichier est mis à jour à chaque fois qu’une modification majeure est apportée au projet. Il sert de référence rapide pour le modèle IA et pour tout développeur entrant dans le projet._
