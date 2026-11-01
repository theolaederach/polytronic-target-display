# To-do – polytronic-target-display

Oct 31, 2026 · @Théo Lädeach
make by claude.ai, with a scan of the git repo

## Priorité 1 – Bugs à corriger

Ces points cassent déjà le fonctionnement : à traiter en premier, ils tiennent en une soirée.

- [x] `database/reader.py` : dans `getShooterNumber` et `getTargetType`, remplacer `WHERE p.GUID = ?` par `WHERE p.id = ?` (la valeur est un id entier depuis le passage guid → id)
- [x] `database/reader.py` : dans `listLastShot`, remplacer `id LIKE ?` par `id = ?` et ajouter `ORDER BY id` à la lecture des tirs
- [x] `database/writer.py` : `start_programm` écrit `"A10"` en dur ; lire le type de cible dans le paquet `_PRCH` (si le champ existe) ou le configurer par cible, sinon B4 ne s'affiche jamais
- [x] `database/writer.py` : corriger `if not None else …` (toujours vrai) dans `start_programm` ; si l'INSERT échoue, ne pas écraser `current_programm_id` par `None`
- [x] `database/writer.py` : dans `start_serie`, si l'INSERT échoue, ne pas laisser les tirs suivants sur l'ancienne série (log + état cohérent)
- [x] `listener.py` : entourer `analyse_data` d'un `try/except` par ligne avec un log, pour qu'une ligne mal formée ne tue plus le thread
- [x] `listener.py` : vérifier `0 <= target_number < len(targets)` avant `targets[target_number]`
- [ ] `server/api/shots.py` : valider `target` (entier, entre 1 et `NumberOfTarget`) ; renvoyer 400/404 au lieu d'une erreur 500 ; `target=0` ne doit plus viser la dernière cible
- [ ] `server/routes/app_routes.py` : supprimer la route `/test` (le template `test.html` n'existe pas, erreur 500)
- [ ] `database/src/create structure.sql` : supprimer `DROP SCHEMA IF EXISTS` (relancer le script efface toutes les données)
- [ ] `database/src/create structure.sql` : retirer `VISIBLE` des index (syntaxe MySQL 8, probablement refusée par MariaDB — à tester sur un vrai serveur)
- [ ] `database/src/create structure.sql` : `shots.score_base10` en `VARCHAR(45)` → type entier ; corriger la faute `taget_number` (colonne, `writer.py` et `listener.py` à adapter ensemble)
- [ ] Renommer le fichier SQL sans espace (`create_structure.sql`) et aligner le chemin dans le README et `doc.md`

## Priorité 2 – Robustesse

Le listener et la base doivent survivre aux paquets étranges, aux doublons et aux connexions mortes.

- [ ] `listener.py` : gérer plusieurs clients (un thread par connexion, `srv.listen(1)` bloque tout derrière un client)
- [ ] `listener.py` : ajouter `settimeout` ou `SO_KEEPALIVE` pour qu'une connexion à moitié morte ne bloque plus le listener
- [ ] `listener.py` : supprimer le code mort (fallback latin-1 jamais atteint avec `errors="replace"`, `except KeyboardInterrupt` inutile dans un thread)
- [ ] Faire de la table `current` la seule source de vérité de l'état des cibles (le listener et Flask modifient aujourd'hui les mêmes `current_*` sans verrou)
- [ ] Décider d'une stratégie pour les GUID : `UNIQUE` global → clé composite avec la date si le système de tir remet ses compteurs à zéro ; logger les doublons au lieu d'un simple `print`
- [ ] Stocker les heures avec la date (`DATETIME` au lieu de `TIME`) avant d'ajouter des statistiques sur plusieurs jours
- [ ] Utiliser `DATABASE_NAME` dans `writer.py` au lieu du schéma `polytronic-target-display` écrit en dur

## Priorité 3 – Sécurité et déploiement

Le plus urgent ici : le débogueur Flask est ouvert sur le réseau.

- [ ] `server/app.py` : `debug=True` avec `host=0.0.0.0` expose le débogueur Werkzeug (exécution de code à distance) ; le rendre configurable dans `.env` avec `False` par défaut
- [ ] Servir l'application avec waitress ou gunicorn en production
- [ ] Restreindre le listener TCP à l'IP du système de tir (allowlist ou pare-feu) : aujourd'hui n'importe qui sur le réseau peut injecter des tirs
- [ ] `main.py` : ne plus tester `.env` par chemin relatif (échoue depuis un autre dossier et exclut les variables d'environnement type Docker ou systemd)

## Priorité 4 – Performance

Chaque poll d'une cible ouvre environ 8 connexions MariaDB, toutes les 2 s, pour 5 cibles et chaque navigateur ouvert.

- [ ] Utiliser un pool de connexions (`mariadb.ConnectionPool`) dans `database/connection.py`
- [ ] Créer un endpoint unique `/api/targets` qui renvoie toutes les cibles en une requête
- [ ] Regrouper les lectures (programme, série, tirs, score) en une requête SQL avec JOIN ; ne plus appeler `update()` 3 fois par poll
- [ ] `update-target.js` : remplacer `setInterval` par un `setTimeout` récursif pour que les requêtes ne s'empilent pas si le serveur ralentit
- [ ] `update-target.js` : ne redessiner que si les données ont changé (évite le clignotement)
- [ ] À terme : passer le polling à SSE ou WebSocket

## Priorité 5 – Qualité, tests et documentation

Aucun test n'existe ; la documentation contredit le code sur plusieurs points.

**Tests et outillage**

- [ ] Séparer le parsing de `analyse_data` de l'appel à la base, puis ajouter pytest (les lignes d'exemple en commentaire servent de cas de test)
- [ ] Ajouter une CI GitHub Actions avec ruff et pytest
- [ ] Remplacer les `print` par `logging` ; corriger « Waring » (3 occurrences dans `reader.py`)
- [ ] Ajouter des `__init__.py` dans `database/` et `server/`
- [ ] Nettoyer le `.gitignore` (les lignes `assets/*` et `/static/target*.png` datent de l'ancienne structure)

**Dépendances**

- [ ] `requirements.txt` : remplacer `dotenv` par `python-dotenv`, retirer `setuptools`, versionner les paquets
- [ ] Documenter que le paquet `mariadb` exige la bibliothèque C MariaDB Connector (ou passer à PyMySQL)

**Documentation**

- [ ] README : remplacer `python app.py` par `python main.py`
- [ ] README : corriger le chemin du fichier SQL et ajouter `HOST_WEB_SERVER` et `PORT_WEB_SERVER` au tableau des variables
- [ ] `doc.md` : l'API renvoie un objet (`shooter_number`, `target_type`, `total_score`, `shots`), pas un tableau
- [ ] `doc.md` : corriger « 1 = most recent » (c'est l'inverse) et aligner la roadmap avec celle du README

**Front-end**

- [ ] `update-target.js` : déclarer `shots` avec `const` (variable globale accidentelle) et corriger le commentaire « 1 seconde » (l'intervalle est de 2000 ms)
- [ ] `target.html` et `target_fs.html` : remplacer les 5 blocs SVG identiques par une boucle Jinja
- [ ] `target_fs.html` : le bloc `.other` n'a pas de SVG, d'où un `console.warn` toutes les 2 s ; ajouter le SVG ou ignorer ce bloc
- [ ] `update-target.js` : changer l'image de la cible même quand il n'y a aucun tir
- [ ] Vérifier que `targetSizeM = 1.0` correspond à l'échelle des images A10 et B4
- [ ] Remplir les liens `href=""` de la navigation et le contenu de `home.html`

## Priorité 6 – Idées fonctionnelles

Une fois les bases solides, ces ajouts couvrent aussi les items ouverts de ta roadmap.

- [ ] Indicateur « dernier paquet reçu il y a X s » et endpoint `/health` pour repérer un listener mort
- [ ] Tableau des scores (la fonction `listScore` existe déjà)
- [ ] Graphiques et statistiques par tireur
- [ ] Diaporama des sponsors
- [ ] Dockerfile et docker-compose (application + MariaDB), pour couvrir l'item « auto-install script »
