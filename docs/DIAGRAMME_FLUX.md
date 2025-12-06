# Diagrammes de Flux

Ce document détaille les différents flux de données et de processus au sein de l'application MLOps.

## 1. 🔄 Flux de Données Global & Métriques

Ce diagramme illustre le cycle de vie complet de la donnée : de l'import initial jusqu'au monitoring, en passant par l'entraînement et l'inférence.

```mermaid
graph LR
    %% Styles
    classDef data fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef process fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px;
    classDef model fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef metric fill:#ffccbc,stroke:#d84315,stroke-width:2px;

    %% Noeuds
    CSV[(Fichiers CSV\nMovieLens)]:::data
    DB[(PostgreSQL\nDonnées)]:::data
    Pipeline[Pipeline\nEntraînement]:::process
    Model{{Modèle\n.pkl}}:::model
    MinIO[(MinIO\nStockage)]:::data
    MLflow[MLflow\nTracking]:::model
    API[API\nInférence]:::process
    Prometheus[(Prometheus\nMétriques)]:::metric

    %% Flux Données (Bleu)
    CSV -->|Import| DB
    DB -->|Load Ratings| Pipeline
    DB -->|Read History| API

    %% Flux Modèles (Vert)
    Pipeline -->|Train| Model
    Model -->|Save Artifact| MinIO
    MinIO -->|Load Model| API

    %% Flux Métriques (Rouge)
    Pipeline -->|Log RMSE/MAE| MLflow
    API -->|Expose /metrics| Prometheus
```

---

## 2. 🚀 Flux d'Entraînement (Training Pipeline)

Détail du processus déclenché par Airflow ou manuellement.

```mermaid
graph TD
    Trigger[Déclencheur\n(Airflow / Manuel)] -->|POST /generate-ratings| Gen[Génération Données]
    Gen -->|POST /training/| API[API FastAPI]
    API -->|Background Task| Pipeline[Pipeline d'Entraînement]
    
    subgraph "Logique d'Entraînement"
        Pipeline -->|1. Load| DB[(PostgreSQL)]
        DB -->|Données Filtrées| Split[Train/Test Split]
        Split -->|2. Train| Models[Entraînement Parallèle\n(SVD, KNN, Baseline)]
        Models -->|3. Evaluate| CV[Cross-Validation 3-fold]
        CV -->|4. Log| MLflow[MLflow Tracking]
        
        MLflow -->|Comparaison| Best{Meilleur que\nProduction?}
        Best -->|Oui| Save[Sauvegarde Modèle]
        Best -->|Non| Discard[Ignorer]
        
        Save -->|Upload| MinIO[(MinIO)]
        Save -->|Register| Registry[MLflow Model Registry]
    end
```

---

## 3. 🎯 Flux de Prédiction (Inférence)

Cheminement d'une requête utilisateur pour obtenir des recommandations.

```mermaid
graph TD
    User((Utilisateur)) -->|POST /predict/| API[API FastAPI]
    
    subgraph "Logique de Prédiction"
        API -->|Check User| DB[(PostgreSQL)]
        DB -->|User Exists?| Condition{Connu?}
        
        Condition -->|Non| ColdStart[Module Cold Start]
        ColdStart -->|Top Popular| Reco1[Recommandations\nGénériques]
        
        Condition -->|Oui| Inference[Chargement Modèle]
        Inference -->|Load .pkl| MinIO[(MinIO)]
        Inference -->|Predict| Reco2[Recommandations\nPersonnalisées]
    end
    
    Reco1 -->|Format JSON| Response[Réponse API]
    Reco2 -->|Format JSON| Response
    
    Response --> User
```

---

## 4. 📊 Flux de Monitoring

Collecte et visualisation des métriques de santé et de performance.

```mermaid
graph LR
    subgraph "Application"
        API[API FastAPI] -->|Middleware| Metrics[Compteurs Prometheus]
        Metrics -->|Expose| Endpoint[/metrics]
    end
    
    subgraph "Observabilité"
        Prometheus[Prometheus] -->|Scrape 15s| Endpoint
        Grafana[Grafana] -->|Query PromQL| Prometheus
        User((Admin)) -->|View Dashboards| Grafana
    end
```

---

## 5. 📉 Flux de Détection de Drift

Analyse de la dérive des données (Data Drift).

```mermaid
graph TD
    Trigger[Cron / Manuel] -->|GET /monitoring/drift| API
    
    subgraph "Drift Detection"
        API -->|1. Load Reference| Baseline[Baseline Stats]
        API -->|2. Load Current| Current[Données Récentes]
        
        Baseline & Current -->|3. Compare| Test[Test Kolmogorov-Smirnov]
        
        Test -->|Drift Detected?| Decision{Drift > Seuil?}
        
        Decision -->|Oui| Alert[Alerte / Rapport Rouge]
        Decision -->|Non| OK[Rapport Vert]
        
        Alert & OK -->|Générer| Report[Rapport HTML Evidently]
    end
    
    Report -->|Sauvegarde| MinIO
```
