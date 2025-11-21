# Projet MLOps - Recommandation de Films

Systeme de recommandation de films base sur MovieLens avec API FastAPI, MLflow, Docker et monitoring.

## Installation

Prerequis: Docker et Docker Compose

```bash
docker compose down -v
docker compose build
docker compose up -d
```

L'import des donnees prend environ 25 minutes. Verifier avec:
```bash
docker logs jun25_bmle_mlops_reco_films-import_data-1
```

## Services

- API: http://localhost:8080
- MLflow: http://localhost:5000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)
- Streamlit: http://localhost:8501

## API

Documentation: http://localhost:8080/docs

### Endpoints

**Entrainement:**
- POST /training/ - Declencher l'entrainement
- GET /training/status - Statut de l'entrainement

**Predictions:**
- POST /predict/ - Obtenir des recommandations (gère le cold start automatiquement)

**Donnees:**
- POST /generate-ratings/?batch_size=X - Generer des votes aleatoires
- GET /get-random-ratings/?n=X - Recuperer des votes aleatoires
- GET /stats - Statistiques sur les donnees

**Monitoring:**
- GET /monitoring/drift - Verifier le data drift
- GET /monitoring/drift/evidently - Rapport Evidently
- POST /monitoring/drift/baseline - Creer une baseline
- GET /monitoring/stats - Statistiques des donnees
- GET /monitoring/recommendations - Statistiques de monitoring
- GET /metrics - Metriques Prometheus

## Pipeline DVC

Le pipeline execute:
1. Verification de la structure
2. Import des donnees brutes
3. Creation du dataset
4. Entrainement du modele
5. Predictions

## Developpement local

Pour travailler sur le code sans Docker:

**Linux/Mac:**
```bash
chmod +x setup_venv.sh
./setup_venv.sh
source venv/bin/activate
```

**Windows:**
```cmd
setup_venv.bat
venv\Scripts\activate
```

## Streamlit

Interface utilisateur pour tester les recommandations.

```bash
pip install -r requirements.txt
streamlit run src/streamlit_app.py
```

## Fonctionnalites

**Cold Start:** Gestion automatique des nouveaux utilisateurs avec recommandations basees sur films populaires et genres.

**Data Drift:** Detection automatique des changements dans les donnees avec comparaison a une baseline.

**Monitoring:** Suivi de la qualite des recommandations (diversite, nouveaute, coverage).

**MLflow:** Comparaison automatique des modeles et promotion vers Production si meilleur.

**Entrainement planifie:** Script cron dans Docker pour execution automatique quotidienne.

**Prometheus/Grafana:** Monitoring des metriques API et ML.

**Evidently:** Detection avancée de derive de donnees.

## Tests

```bash
pytest tests/
```

## Structure

```
├── docker/              # Dockerfiles
├── src/
│   ├── api/            # API FastAPI
│   ├── data/           # Import et traitement
│   ├── models/         # Entrainement et prediction
│   └── pipeline/       # Pipeline DVC avec MLflow
├── data/               # Donnees brutes
├── models/             # Modeles entraines
└── docker-compose.yml # Configuration services
```
