# Gloria.Dev — Portfolio Flask

Application portfolio personnelle bilingue (FR/EN) avec thème clair/sombre, code animé, assistant de présentation, CV visualisable/téléchargeable et administration privée.

## Fonctionnalités
- Portfolio public responsive.
- Français / English.
- Mode sombre / clair (préférence conservée dans le navigateur).
- CV PDF : visualisation dans le navigateur et téléchargement.
- Administration protégée : profil, liens sociaux, photo, projets, formations et remplacement du CV.
- Assistant de présentation avec réponses basées sur les sections du portfolio (pas un modèle IA externe).
- Données du portfolio stockées dans une base SQLite `instance/gloria.db`, gérée par SQLAlchemy.
- Migration automatique des données de l’ancien fichier `instance/portfolio.json` au premier démarrage si la base SQLite n’existe pas encore.

## Installation
Python 3.10+ recommandé.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
python -m pip install -r requirements.txt
python setup.py
python app.py
```
Ouvre ensuite `http://127.0.0.1:5000`.

## Déploiement sur le service Render existant

Le dépôt peut remplacer le code du service Render existant sans créer un nouveau service. Le fichier `Procfile` lance l’application avec Gunicorn. Configure la commande de build `pip install -r requirements.txt` et la commande de démarrage `gunicorn app:app`. Avant le premier déploiement, ajoute dans **Render → service → Environment** `ADMIN_USERNAME` et `ADMIN_PASSWORD` avec tes identifiants forts (12 caractères minimum). Ne les partage pas et ne les ajoute jamais au dépôt. L’application refuse de démarrer sur Render si ces variables ne sont pas configurées et désactive la création publique de compte admin.

Sur l’offre gratuite, aucun service externe ou stockage additionnel n’est nécessaire. L’application utilise SQLite et stocke les fichiers localement ; l’identifiant administrateur reste sécurisé dans les variables d’environnement Render. Render Free n’ayant pas de disque persistant, les changements effectués dans l’admin (profil, photo, CV et images) peuvent être perdus lors d’un redémarrage ou d’un redéploiement. Pour garder ces changements durablement, il faudra ultérieurement choisir un disque Render payant ou configurer un stockage externe.

## Création du compte administrateur (une seule fois)

1. Au premier lancement, ouvre `http://127.0.0.1:5000/admin/setup`.
2. Crée ton identifiant personnel et un mot de passe fort d’au moins 12 caractères.
3. Tu seras automatiquement connectée au tableau de bord privé.
4. Après la création du compte, `/admin/setup` renvoie une page introuvable (404) : personne ne peut créer un deuxième compte. Il n’existe pas d’inscription publique.
5. Pour les visites suivantes, utilise `http://127.0.0.1:5000/admin/login`.

Les pages d’administration redirigent les visiteurs non connectés vers la connexion. Les identifiants sont stockés dans `instance/admin.json` avec le mot de passe sous forme de hash. **Ne partage pas ce fichier, `instance/secret_key.txt`, `instance/gloria.db` ni tes identifiants.**

Avant de déployer en production, utilise HTTPS, un serveur WSGI et configure une variable d’environnement `SECRET_KEY` longue et aléatoire.

Le CV fourni est inclus dans le dossier de l'application. Depuis **Espace admin → Gestion du CV**, tu peux le remplacer par un PDF de 12 Mo maximum. Les boutons publics pointent automatiquement vers le dernier CV enregistré.

## Personnalisation
- Les informations initiales sont dans `app.py` sous `DEFAULT_DATA`.
- Les modifications sont enregistrées dans `instance/gloria.db` via SQLAlchemy. Si un ancien `instance/portfolio.json` est présent et que la base n’existe pas encore, son contenu est importé automatiquement au démarrage.
- Les URLs GitHub et LinkedIn du CV n'étaient pas indiquées sous forme de liens complets ; remplace les liens génériques depuis l'administration.
- La photo de profil n'étant pas incluse séparément dans le CV, ajoute-la depuis l'administration.
- Le chatbot actuel est un assistant de portfolio à réponses prédéfinies. Pour utiliser un vrai LLM, il faudra ajouter un fournisseur et gérer sa clé API côté serveur.

## Structure
- `app.py` : routes, authentification et logique serveur.
- `templates/index.html` : site public.
- `templates/admin.html` : tableau de bord.
- `templates/login.html` : connexion.
- `templates/setup_admin.html` : création unique du compte propriétaire.
- `static/css/style.css` : design responsive.
- `static/js/site.js` : animation du code, thèmes et assistant.
- `static/uploads/` : CV et photo mis à jour.
- `instance/gloria.db` : base de données SQLite (profil, compétences, projets, expériences, formations et paramètres du site).
- `instance/portfolio.json` : ancien format, utilisé seulement pour la migration initiale si présent.

## Notes de sécurité
Aucun mot de passe administrateur par défaut n’est fourni. Crée ton compte lors de la configuration initiale. Ne déploie pas l’application publiquement sans sécuriser le serveur. Pour un site public, utilise une clé secrète forte, HTTPS, un serveur WSGI de production, et ajoute idéalement une protection CSRF et une politique de sauvegarde.


## Sauvegarde
Arrête l’application avant de sauvegarder, puis copie le dossier `instance/` (base SQLite, compte administrateur et clé de session) ainsi que `static/uploads/` (CV et photos). Ne publie jamais ces fichiers. Si tu remplaces le projet par une nouvelle version, conserve ces données et sauvegarde-les avant toute migration.
