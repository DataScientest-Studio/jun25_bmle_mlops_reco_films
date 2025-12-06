# Projet MLOps - Recommandation de Films 🎬

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)
[![MLflow](https://img.shields.io/badge/MLflow-Tracking-orange.svg)](https://mlflow.org/)

Système complet de recommandation de films utilisant les pratiques MLOps modernes, basé sur le **dataset MovieLens 20M** (~20 millions d'évaluations). Pipeline automatisé d'entraînement, déploiement et monitoring de modèles de machine learning.

---

## 🚀 Démarrage Rapide

### Prérequis
- Docker et Docker Compose
- 8 Go de RAM minimum
- 10 Go d'espace disque libre

### Installation

```bash
# Cloner le repository
git clone <repository-url>
cd jun25_bmle_mlops_reco_films

# Démarrer tous les services
docker compose down -v
docker compose build
docker compose up -d
```

### Import des données

L'import des données MovieLens 20M prend environ **25 minutes**. Suivre la progression :

```bash
docker logs -f jun25_bmle_mlops_reco_films-import_data-1
```

---

## 🌐 Services Disponibles

| Service | URL | Credentials | Description |
|---------|-----|-------------|-------------|
| **Streamlit** | http://localhost:8501 | - | Interface utilisateur principale |
| **API FastAPI** | http://localhost:8080 | - | API REST |
| **API Docs** | http://localhost:8080/docs | - | Documentation interactive Swagger |
| **MLflow** | http://localhost:5000 | - | Tracking des expériences ML |
| **Airflow** | http://localhost:8081 | admin/admin | Orchestration des pipelines |
| **Grafana** | http://localhost:3001 | admin/admin | Dashboards de monitoring |
| **Prometheus** | http://localhost:9090 | - | Métriques système |
| **MinIO Console** | http://localhost:9001 | minioadmin/minioadmin123 | Stockage S3 |
| **PgAdmin** | http://localhost:5050 | - | Administration PostgreSQL |

---

## 📊 Architecture

Le système est composé de plusieurs microservices orchestrés avec Docker Compose :

### Services Backend
- **PostgreSQL** (port 5432) : Base de données principale (20M évaluations)
- **MinIO** (ports 9000, 9001) : Stockage S3-compatible pour artefacts MLflow
- **MLflow** (port 5000) : Tracking des expériences et registry de modèles
- **API FastAPI** (port 8080) : API REST pour prédictions et entraînement

### Services Monitoring & Orchestration
- **Prometheus** (port 9090) : Collecte de métriques
- **Grafana** (port 3001) : Visualisation des métriques
- **Airflow** (port 8081) : Orchestration quotidienne (entraînement à 2h)
- **Streamlit** (port 8501) : Interface utilisateur web

### Flux de Données

```
1. Données : CSV → PostgreSQL (import_data.py)
2. Entraînement : PostgreSQL → train_model_pipeline.py → MLflow → MinIO
3. Modèle : MLflow → models/model.pkl (local)
4. Prédiction : model.pkl + PostgreSQL → predict_model_pipeline.py → API
5. Interface : Streamlit → API → Utilisateur
6. Monitoring : API → Prometheus → Grafana
7. Orchestration : Airflow → API → Entraînement quotidien
```

Pour plus de détails, voir [ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 🔌 API Endpoints

Documentation complète : http://localhost:8080/docs

### Entraînement

```bash
# Déclencher un entraînement
curl -X POST http://localhost:8080/training/ \
  -H "Content-Type: application/json" \
  -d '{"force": true}'

# Vérifier le statut
curl http://localhost:8080/training/status
```

### Prédictions

```bash
# Obtenir des recommandations pour un utilisateur
curl -X POST http://localhost:8080/predict/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "n_recommendations": 10}'
```

### Monitoring

```bash
# Vérifier le data drift
curl http://localhost:8080/monitoring/drift

# Obtenir les statistiques
curl http://localhost:8080/monitoring/stats

# Rapport Evidently
curl http://localhost:8080/monitoring/drift/evidently
```

### Données

```bash
# Statistiques de la base de données
curl http://localhost:8080/stats

# Générer des évaluations aléatoires
curl -X POST "http://localhost:8080/generate-ratings/?batch_size=1000"
```

---

## 🤖 Modèles de Machine Learning

Le système entraîne et compare automatiquement 3 modèles :

| Modèle | Description | Avantages |
|--------|-------------|-----------|
| **SVD** | Singular Value Decomposition | Haute précision, factorisation matricielle |
| **KNNBasic** | K-Nearest Neighbors | Recommandations basées sur similarité |
| **NormalPredictor** | Baseline aléatoire | Référence de comparaison |

Le meilleur modèle est automatiquement sélectionné basé sur le **RMSE** (Root Mean Square Error) et enregistré dans MLflow.

---

## ✨ Fonctionnalités MLOps

### 🆕 Cold Start
Gestion automatique des nouveaux utilisateurs avec recommandations basées sur :
- Films les plus populaires
- Genres préférés (si disponibles)
- Diversité des recommandations

### 📈 Data Drift Detection
- Détection automatique des changements dans les données
- Comparaison avec une baseline de référence
- Rapports Evidently détaillés
- Alertes automatiques

### 📊 Monitoring
Suivi de la qualité des recommandations :
- **Diversité** : Variété des genres recommandés
- **Nouveauté** : Proportion de films récents
- **Coverage** : Pourcentage du catalogue couvert
- **Métriques Prometheus** : Latence, throughput, erreurs

### 🔄 MLflow Integration
- Tracking automatique de tous les entraînements
- Comparaison des modèles (RMSE, MAE)
- Registry de modèles avec versioning
- Promotion automatique vers Production si amélioration
- Stockage des artefacts dans MinIO (S3)

### ⏰ Entraînement Planifié
- DAG Airflow pour entraînement quotidien (2h du matin)
- Vérification de santé de l'API avant exécution
- Logs détaillés et gestion d'erreurs
- Notifications en cas d'échec

### 📉 Prometheus & Grafana
- Métriques API : requêtes/sec, latence, erreurs
- Métriques ML : RMSE, MAE, temps d'entraînement
- Dashboards pré-configurés
- Alerting personnalisable

---

## 🛠️ Développement Local

Pour travailler sur le code sans Docker :

### Linux/Mac
```bash
chmod +x setup_venv.sh
./setup_venv.sh
source venv/bin/activate
pip install -r requirements.txt
```

### Windows
```cmd
setup_venv.bat
venv\Scripts\activate
pip install -r requirements.txt
```

### Lancer Streamlit localement
```bash
streamlit run src/streamlit_app.py
```

---

## 🧪 Tests

```bash
# Lancer tous les tests
pytest tests/

# Tests avec coverage
pytest tests/ --cov=src --cov-report=html

# Tests spécifiques
pytest tests/test_api.py
pytest tests/test_pipeline.py
```

---

## 📁 Structure du Projet

```
jun25_bmle_mlops_reco_films/
├── docker/                      # Dockerfiles et configurations
│   ├── api/                     # Dockerfile API FastAPI
│   ├── streamlit/               # Dockerfile Streamlit
│   ├── mlflow/                  # Configuration MLflow
│   ├── import_data/             # Scripts d'import
│   ├── prometheus/              # Configuration Prometheus
│   └── grafana/                 # Dashboards Grafana
├── src/
│   ├── api/                     # API FastAPI
│   │   ├── endpoints/           # Routers (training, predict, monitoring, data)
│   │   ├── app.py               # Application principale
│   │   ├── cold_start.py        # Gestion cold start
│   │   ├── data_drift.py        # Détection drift
│   │   └── monitoring.py        # Métriques qualité
│   ├── data/
│   │   └── sql/                 # Scripts SQL et import
│   ├── pipeline/                # Pipelines ML
│   │   ├── train_model_pipeline.py
│   │   ├── predict_model_pipeline.py
│   │   ├── data_loader.py
│   │   └── config.yaml
│   ├── pages/                   # Pages Streamlit
│   └── streamlit_app.py         # Application Streamlit
├── dags/                        # DAGs Airflow
│   └── training_dag.py
├── data/                        # Données brutes (CSV)
├── models/                      # Modèles entraînés
├── predictions/                 # Prédictions sauvegardées
├── metrics/                     # Métriques exportées
├── tests/                       # Tests unitaires
├── docs/                        # Documentation
│   └── ARCHITECTURE.md          # Architecture détaillée
├── docker-compose.yml           # Orchestration services
├── requirements.txt             # Dépendances Python
└── README.md                    # Ce fichier
```

---

## 🔧 Technologies Utilisées

### Backend & API
- **Python 3.11** : Langage principal
- **FastAPI** : Framework API REST
- **PostgreSQL 16** : Base de données
- **SQLAlchemy** : ORM Python

### Machine Learning
- **scikit-surprise** : Modèles de recommandation (SVD, KNN)
- **pandas** : Manipulation de données
- **numpy** : Calculs numériques

### MLOps & Tracking
- **MLflow** : Tracking expériences et registry
- **DVC** : Versioning données et modèles
- **MinIO** : Stockage S3-compatible

### Monitoring & Observabilité
- **Prometheus** : Collecte de métriques
- **Grafana** : Visualisation
- **Evidently** : Data drift detection

### Orchestration & UI
- **Apache Airflow** : Orchestration pipelines
- **Streamlit** : Interface utilisateur
- **Docker & Docker Compose** : Containerisation

---

## 📖 Documentation Complémentaire

- [Architecture détaillée](docs/ARCHITECTURE.md) : Flux de données, composants, diagrammes
- [API Documentation](http://localhost:8080/docs) : Documentation interactive Swagger
- [MLflow UI](http://localhost:5000) : Expériences et modèles
- [Grafana Dashboards](http://localhost:3001) : Métriques et monitoring

---

## 🐛 Dépannage

### Les conteneurs ne démarrent pas
```bash
# Vérifier les logs
docker compose logs

# Redémarrer proprement
docker compose down -v
docker compose up -d
```

### L'import de données est bloqué
```bash
# Vérifier les logs d'import
docker logs -f jun25_bmle_mlops_reco_films-import_data-1

# Relancer l'import
docker compose restart import_data
```

### L'API ne répond pas
```bash
# Vérifier la santé de l'API
curl http://localhost:8080/health

# Vérifier les logs
docker logs -f api
```

### Airflow ne démarre pas
```bash
# Vérifier que PostgreSQL est prêt
docker logs db

# Réinitialiser Airflow
docker compose restart airflow-webserver airflow-scheduler
```

---

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 👥 Contributeurs

Projet MLOps - DataScientest - Promotion Juin 2025

---

## 📚 Dataset

Ce projet utilise le dataset **MovieLens 20M** :
- ~20 millions d'évaluations
- ~27 000 films
- ~138 000 utilisateurs
- Période : 1995-2015

Source : [GroupLens Research](https://grouplens.org/datasets/movielens/)
