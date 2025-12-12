# Contexte

Le projet StreamFlow dispose actuellement d'une base de données PostgreSQL structurée contenant des snapshots mensuels validés pour deux périodes (31 janvier et 29 février 2024). Ces données couvrent l'intégralité du parcours client : informations sociodémographiques (users), détails contractuels (subscriptions), métriques d'usage technique (usage_agg_30d), historique des paiements (payments_agg_90d) et interactions avec le support (support_agg_90d).

L'objectif de ce TP est d'intégrer Feast comme Feature Store centralisé pour connecter ces données brutes aux modèles de Machine Learning. Nous allons définir les entités et les vues de features, réaliser une récupération offline pour constituer un jeu de données d'entraînement (Training Dataset), puis matérialiser ces features dans un Online Store pour les exposer en temps réel via une API FastAPI, garantissant ainsi la cohérence entre l'environnement d'entraînement et la production.

# Mise en place de Feast

Question 2.d.

Collez la commande exacte que vous avez utilisée pour démarrer les services : docker compose up -d --build

Écrivez 2–3 lignes expliquant le rôle du conteneur feast :

Le conteneur feast agit comme l'environnement d'administration du Feature Store.

- où se trouve la configuration du Feature Store dans le conteneur : la configuration du dépôt (fichiers .py et .yaml) est montée dans le dossier /repo du conteneur.

- comment vous allez l’utiliser (via docker compose exec feast ... pour lancer feast apply et feast materialize) : ce conteneur ne lance pas de service réseau (API) par lui-même pour l'instant, il tourne en boucle (tail -f /dev/null) pour nous permettre d'exécuter les commandes CLI de Feast. Nous l'utiliserons via docker compose exec feast <commande> pour enregistrer les définitions (feast apply) et synchroniser les données vers le store en ligne (feast materialize).

# Définition du Feature Store

Question 3.a.

ce qu’est une Entity dans Feast : dans Feast, une Entity représente un concept métier (comme un client, un produit ou un véhicule) auquel on rattache des données. Elle définit la clé primaire logique.

pourquoi user_id est un bon choix de clé de jointure pour StreamFlow : ici, nous avons choisi user_id comme clé de jointure (join_key) car c'est l'identifiant unique commun à toutes nos tables PostgreSQL (snapshots). C'est le pivot qui permettra à Feast de relier automatiquement les informations de facturation, d'usage et de support pour un même individu à une date donnée.

Question 3.b.

Data Sources (PostgreSQL) : les sources de données connectent Feast aux tables de snapshots créées lors du TP2.

Par exemple, la source usage_agg_30d_source pointe vers la table usage_agg_30d_snapshots et expose des métriques comportementales clés telles que :
- watch_hours_30d : Nombre d'heures de visionnage sur le dernier mois.
- unique_devices_30d : Nombre d'appareils différents utilisés.
- rebuffer_events_7d : Nombre d'événements de chargement (buffering) sur la dernière semaine (indicateur de frustration technique). Le champ as_of est systématiquement utilisé comme timestamp_field pour gérer l'historisation.

Question 3.c.

Application de la configuration (feast apply) : la commande feast apply est l'équivalent d'un "commit" pour l'infrastructure du Feature Store. Elle analyse les fichiers de définition Python (entities.py, feature_views.py, etc.), valide la cohérence du graphe de features, et enregistre cette configuration dans le fichier local registry.db. C'est cette base de registre qui servira de vérité terrain pour les clients (SDK) souhaitant récupérer des données.

# Récupération offline & online

Ajoutez la commande que vous avez utilisée : docker compose exec prefect python build_training_dataset.py

Montrez les 5 premières lignes du fichier à l’aide de :

kilia@LEGION-Kilian:~/tpdocker$ head -5 data/processed/training_df.csv
user_id,event_timestamp,months_active,monthly_fee,paperless_billing,watch_hours_30d,avg_session_mins_7d,failed_payments_90d,churn_label
7114-AEOZE,2024-01-31,60,19.85,False,30.923343651468,29.141044640845102,0,False
0754-EEBDC,2024-01-31,4,19.900000000000002,False,28.5548009981467,29.141044640845102,0,False
3413-BMNZE,2024-01-31,1,45.25,False,32.0919931169304,29.141044640845102,0,False
8865-TNMNX,2024-01-31,10,49.550000000000004,False,27.9848207162474,29.141044640845102,0,False

Question 4.e.

kilia@LEGION-Kilian:~/tpdocker$ docker compose exec feast feast materialize 2024-01-01T00:00:00 2024-02-01T00:00:00
/usr/local/lib/python3.11/site-packages/feast/repo_config.py:278: DeprecationWarning: The serialization version below 3 are deprecated. Specifying `entity_key_serialization_version` to 3 is recommended.
  warnings.warn(
Materializing 4 feature views from 2024-01-01 00:00:00+00:00 to 2024-02-01 00:00:00+00:00 into the postgres online store.

payments_agg_90d_fv:
/usr/local/lib/python3.11/site-packages/feast/infra/key_encoding_utils.py:141: UserWarning: Serialization of entity key with version < 3 is removed. Please use version 3 by setting entity_key_serialization_version=3.To reserializa your online store featrues refer -  https://github.com/feast-dev/feast/blob/master/docs/how-to-guides/entity-reserialization-of-from-v2-to-v3.md
  warnings.warn(
support_agg_90d_fv:
/usr/local/lib/python3.11/site-packages/feast/infra/key_encoding_utils.py:141: UserWarning: Serialization of entity key with version < 3 is removed. Please use version 3 by setting entity_key_serialization_version=3.To reserializa your online store featrues refer -  https://github.com/feast-dev/feast/blob/master/docs/how-to-guides/entity-reserialization-of-from-v2-to-v3.md
  warnings.warn(
usage_agg_30d_fv:
/usr/local/lib/python3.11/site-packages/feast/infra/key_encoding_utils.py:141: UserWarning: Serialization of entity key with version < 3 is removed. Please use version 3 by setting entity_key_serialization_version=3.To reserializa your online store featrues refer -  https://github.com/feast-dev/feast/blob/master/docs/how-to-guides/entity-reserialization-of-from-v2-to-v3.md
  warnings.warn(
subs_profile_fv:
/usr/local/lib/python3.11/site-packages/feast/infra/key_encoding_utils.py:141: UserWarning: Serialization of entity key with version < 3 is removed. Please use version 3 by setting entity_key_serialization_version=3.To reserializa your online store featrues refer -  https://github.com/feast-dev/feast/blob/master/docs/how-to-guides/entity-reserialization-of-from-v2-to-v3.md
  warnings.warn(

Question 4.d.

Temporal Correctness (Point-in-Time Correctness) : 

Feast garantit la cohérence temporelle grâce à un mécanisme de jointure spécifique ("point-in-time join").

1. Dans nos DataSources, nous avons défini timestamp_field="as_of", indiquant la date de validité de chaque donnée.

2. Dans notre entity_df, nous fournissons pour chaque utilisateur un event_timestamp cible (ici le 31 janvier). Pour chaque ligne, Feast recherche automatiquement la valeur de feature la plus récente dans la source, à condition que son as_of soit inférieur ou égal à l'event_timestamp. Cela rend impossible l'utilisation de données futures (Data Leakage) lors de la constitution du jeu d'entraînement.

Question 4.f.

kilia@LEGION-Kilian:~/tpdocker$ docker compose exec feast python /repo/debug_online_features.py
/usr/local/lib/python3.11/site-packages/feast/repo_config.py:278: DeprecationWarning: The serialization version below 3 are deprecated. Specifying `entity_key_serialization_version` to 3 is recommended.
  warnings.warn(
/usr/local/lib/python3.11/site-packages/feast/infra/key_encoding_utils.py:141: UserWarning: Serialization of entity key with version < 3 is removed. Please use version 3 by setting entity_key_serialization_version=3.To reserializa your online store featrues refer -  https://github.com/feast-dev/feast/blob/master/docs/how-to-guides/entity-reserialization-of-from-v2-to-v3.md
  warnings.warn(
{'user_id': ['7590-VHVEG'], 'monthly_fee': [29.850000381469727], 'paperless_billing': [True], 'months_active': [1]}

Question 4.g.

copiez le dictionnaire retourné par get_online_features pour un utilisateur (sortie du script) ;

{
  "user_id": ["7590-VHVEG"],
  "subs_profile_fv:months_active": [1],
  "subs_profile_fv:monthly_fee": [29.850000381469727],
  "subs_profile_fv:paperless_billing": [true],
}

Cas d'un utilisateur inconnu :
Si nous interrogeons un user_id qui n'existe pas ou qui n'a pas de données dans la fenêtre de temps matérialisée, Feast ne lève pas d'erreur. Il retourne simplement un dictionnaire contenant l'ID demandé et des valeurs None pour toutes les features. C'est un comportement sécurisé pour la production : c'est au modèle ou à l'application de gérer ces valeurs manquantes (imputation ou valeur par défaut) sans faire crasher le service.

Question 4.j.

Choisissez un user_id pour lequel vous savez que des features existent (par ex. un user du CSV data/seeds/month_000/users.csv). Interrogez l’endpoint /features/{user_id} :

`curl http://localhost:8000/features/7590-VHVEG`

kilia@LEGION-Kilian:~/tpdocker$ curl http://localhost:8000/features/7590-VHVEG
{"user_id":"7590-VHVEG","features":{"user_id":"7590-VHVEG","paperless_billing":true,"months_active":1,"monthly_fee":29.850000381469727}}

# Réflexion

Réduction du Training-Serving Skew :
Le endpoint /features/{user_id} interroge le Online Store de Feast, qui est alimenté par les mêmes définitions (Feature Views) et les mêmes données sources que celles utilisées pour générer le jeu d'entraînement via l'Offline Store.
Cette architecture unifiée garantit que les features servies en production sont calculées exactement de la même manière que lors de l'apprentissage. Cela élimine le risque de divergence (skew) où le modèle recevrait des données mal formatées ou calculées différemment en temps réel, ce qui dégraderait ses performances.

Fin de TP tagué tp3 dans github