# Projet MLOps - Recommandation de Films

Projet MLOps pour un système de recommandation de films basé sur le dataset MovieLens.

## Structure du projet

```
├── docker/              # Dockerfiles pour les services
├── src/
│   ├── api/            # API FastAPI (training, predict, data)
│   ├── data/           # Scripts d'import et traitement des données
│   ├── models/          # Scripts d'entraînement et prédiction
│   └── pipeline/        # Pipeline DVC avec MLflow
├── data/                # Données brutes et traitées
├── models/              # Modèles entraînés
└── docker-compose.yml   # Configuration des services
```

## Démarrage

### Prérequis
- Docker et Docker Compose
- Git

### Lancement

```bash
# Arrêter les services existants
docker compose down -v

# Construire les images
docker compose build

# Lancer les conteneurs
docker compose up -d

# Vérifier l'import des données (attendre ~25 minutes)
docker logs jun25_bmle_mlops_reco_films-import_data-1
```

L'API est accessible sur http://localhost:8080

## API

Documentation interactive : http://localhost:8080/docs

### Endpoints principaux

- `POST /training/` - Déclencher l'entraînement
- `GET /training/status` - Statut de l'entraînement
- `POST /predict/` - Obtenir des recommandations
- `POST /generate-ratings/?batch_size=X` - Générer des votes aléatoires
- `GET /get-random-ratings/?n=X` - Récupérer des votes aléatoires
- `GET /stats` - Statistiques sur les données

## Pipeline

Le pipeline DVC exécute les étapes suivantes :
1. Vérification de la structure
2. Import des données brutes
3. Création du dataset
4. Entraînement du modèle
5. Prédictions

## Services

- PostgreSQL : Base de données (port 5432)
- MLflow : Tracking des expériences (port 5000)
- MinIO : Stockage S3 (ports 9000, 9001)
- API : Service FastAPI (port 8080)
