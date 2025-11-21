# Architecture du Système de Recommandation de Films

## Vue d'ensemble

Le système est composé de plusieurs microservices orchestrés avec Docker Compose.

## Diagramme d'Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL  │  │    MinIO     │  │    MLflow    │          │
│  │   (Port 5432)│  │ (Port 9000)  │  │ (Port 5000)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                 │                 │                  │
│         └─────────────────┴─────────────────┘                  │
│                           │                                     │
│  ┌──────────────────────────────────────────────────────┐     │
│  │                    API FastAPI                        │     │
│  │                   (Port 8080)                         │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │     │
│  │  │ Training │  │ Predict  │  │ Monitoring│           │     │
│  │  │  Endpoint│  │ Endpoint │  │ Endpoint │           │     │
│  │  └──────────┘  └──────────┘  └──────────┘           │     │
│  │                                                       │     │
│  │  - Cold Start Handler                                 │     │
│  │  - Data Drift Detection                               │     │
│  │  - Prometheus Metrics                                │     │
│  └──────────────────────────────────────────────────────┘     │
│                           │                                     │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              Pipeline DVC                             │     │
│  │  - Import Data                                        │     │
│  │  - Train Model                                        │     │
│  │  - Predict                                            │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Prometheus  │  │   Grafana    │  │  Streamlit   │          │
│  │ (Port 9090)  │  │ (Port 3000)  │  │ (Port 8501)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Flux de Données

### 1. Pipeline d'Entraînement

```
PostgreSQL (Ratings) 
    ↓
Pipeline DVC (Train Model)
    ↓
MLflow (Logging + Registry)
    ↓
MinIO (Artifacts Storage)
    ↓
Modèle Sauvegardé (models/best_svd_model.pkl)
```

### 2. Pipeline de Prédiction

```
Requête API (/predict/)
    ↓
Cold Start Check
    ├─ Nouvel utilisateur → Films populaires
    └─ Utilisateur existant → Modèle ML
    ↓
Recommandations
    ↓
Logging (Monitoring)
    ↓
Réponse JSON
```

### 3. Monitoring

```
API Endpoints
    ↓
Prometheus Metrics (/metrics)
    ↓
Grafana Dashboards
    ↓
Visualisation
```

## Services et Ports

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Base de données |
| MinIO | 9000, 9001 | Stockage S3 |
| MLflow | 5000 | Tracking des expériences |
| API FastAPI | 8080 | API REST |
| Prometheus | 9090 | Métriques |
| Grafana | 3000 | Dashboards |
| Streamlit | 8501 | Interface utilisateur |
| PgAdmin | 5050 | Administration DB |

## Technologies Utilisées

- **Backend**: FastAPI, Python 3.11
- **Base de données**: PostgreSQL 16
- **ML**: scikit-surprise (SVD, KNNBasic)
- **Tracking**: MLflow
- **Stockage**: MinIO (S3-compatible)
- **Versioning**: DVC
- **Monitoring**: Prometheus, Grafana
- **Data Drift**: Evidently
- **Frontend**: Streamlit

## Flux de Déploiement

1. **Initialisation**: Docker Compose démarre tous les services
2. **Import des données**: Script d'import charge les données dans PostgreSQL
3. **Entraînement**: Pipeline DVC entraîne le modèle et le logge dans MLflow
4. **API**: FastAPI expose les endpoints pour prédictions et monitoring
5. **Monitoring**: Prometheus collecte les métriques, Grafana les visualise
6. **Frontend**: Streamlit permet l'interaction utilisateur

