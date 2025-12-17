**Exercice 1 : Mise en route + rappel de contexte (sanity checks + où on en est dans la pipeline)**

Question 1.a. Démarrez la stack Docker Compose et vérifiez que les conteneurs principaux démarrent sans erreur.

ok

Question 1.b. Ajoutez le service MLflow dans docker-compose.yml, puis redémarrez la stack.

MLflow ok

Question 1.c. Vérifiez l’accessibilité des interfaces et endpoints suivants : MLfiow UI (localhost:5000), API /health (localhost:8000).

Question 1.d. Faites un smoke check : vérifiez que la récupération de features online fonctionne toujours via l’endpoint existant /features/{user_id}.

Question 1.e. Dans votre rapport reports/rapport_tp4.md, listez :
1. les commandes utilisées,

Relancer les services pour commencer le TP
docker compose up --build

Relancer les services pour prise en compte de MLflow dans docker-compose.yml
docker compose up -d --build

Check des features toujours accessible :
curl http://localhost:8000/features/7590-VHVEG


2. une preuve que chaque service est accessible (captures ou sortie terminal),

Services ok :

kilia@LEGION-Kilian:~/tpdocker$ docker compose ps

NAME                  IMAGE              COMMAND                  SERVICE    CREATED      STATUS         PORTS
tpdocker-api-1        tpdocker-api       "uvicorn app:app --h…"   api        4 days ago   Up 3 minutes   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
tpdocker-feast-1      tpdocker-feast     "bash -lc 'tail -f /…"   feast      4 days ago   Up 3 minutes
tpdocker-postgres-1   postgres:16        "docker-entrypoint.s…"   postgres   5 days ago   Up 3 minutes   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
tpdocker-prefect-1    tpdocker-prefect   "/usr/bin/tini -g --…"   prefect    4 days ago   Up 8 seconds

MLflow :

![alt text](image_tp4/imagetp41c.png)

Check feature ok :
kilia@LEGION-Kilian:~/tpdocker$ curl http://localhost:8000/features/7590-VHVEG
{"user_id":"7590-VHVEG","features":{"user_id":"7590-VHVEG","monthly_fee":29.850000381469727,"months_active":1,"paperless_billing":true}}

3. un court paragraphe : “quels composants tournent et pourquoi”.

PostgreSQL : Sert de stockage persistant pour les données brutes et les snapshots historiques.
Prefect : Orchestre et supervise l'exécution des pipelines d'ingestion et de validation de données.
Feast : Assure la gestion unifiée des features, garantissant la cohérence entre l'entraînement (Offline) et la production (Online).
API (FastAPI) : Expose les données (et bientôt les prédictions) via des endpoints HTTP pour les applications clientes.
MLflow : Centralise le suivi des expériences (tracking) et gère le registre des modèles pour le déploiement.

**Exercice 2 : Créer un script d’entraînement + tracking MLflow (baseline RandomForest)**

Question 2.a. Créez le fichier services/prefect/train_baseline.py et copiez le squelette ci-dessous. Complétez
ensuite les zones marquées par _______ (ce sont vos TODO).

Pour répondre au TODO 9 il faut utiliser `pipe` (le pipeline complet) et non seulement `clf` (le classifieur RandomForest) car le modèle RandomForest ne sait traiter que des données numériques. Or, nos données brutes contiennent des variables catégorielles. Le Pipeline (`pipe`) contient l'étape de pré-traitement (`ColumnTransformer` + `OneHotEncoder`) qui transforme le texte en chiffres, puis le classifieur. En enregistrant le pipeline entier, nous garantissons que le modèle en production sera capable d'accepter des données brutes et de les transformer lui-même. C'est le principe d'un artefact autonome (self-contained).

Question 2.b. Exécutez votre script train_baseline.py dans le conteneur prefect sur month_000 avec

![alt text](image_tp4/imagetp42c.png)

Question 2.c. Dans votre rapport reports/rapport_tp4.md, indiquez :

Suite à l'exécution du script `train_baseline.py`, voici les détails de l'expérience enregistrée :

1.  Date de référence (AS_OF) : `2024-01-31`
2.  Taille du dataset : 7043 lignes
3.  Colonnes catégorielles détectées : `['net_service']`
4.  Métriques de performance :
        - AUC : 0.8227
        - F1-score : 0.5159
        - Accuracy : 0.7836
        - Temps d'entraînement : 1.0232 s (visible dans l'UI MLflow).

Question 2.d. Toujours dans le rapport, expliquez en 5–8 lignes pourquoi on fixe :
- AS_OF et
- random_state

On fixe ces paramètres afin d'isoler les causes de variation des performances :

- `AS_OF` (Reproductibilité des Données) : Il fige l'état temporel du dataset. Sans lui, ré-exécuter le script demain inclurait de nouvelles données ou des modifications, rendant impossible la comparaison équitable avec une version précédente du modèle. Cela garantit que le dataset d'entrée est constant.
- `random_state` (Reproductibilité de l'Algorithme) : Il fige l'aléatoire des calculs (split train/val, échantillonnage du Random Forest). Sans lui, deux exécutions successives sur les mêmes données produiraient des métriques différentes juste par "chance".

