# Diagrammes de Flux

## Flux d'Entraînement

```
┌─────────────┐
│   Déclenche │
│  POST /training/ │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Background Task │
└──────┬──────────┘
       │
       ▼
┌──────────────────────┐
│ Charger données DB    │
│ (PostgreSQL)         │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Filtrer utilisateurs │
│ et films            │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Évaluer modèles      │
│ (SVD, KNN, Random)   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ GridSearch SVD       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Comparer avec modèle │
│ précédent (MLflow)    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Enregistrer dans     │
│ MLflow Registry      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Promouvoir vers      │
│ Production si meilleur│
└──────────────────────┘
```

## Flux de Prédiction

```
┌─────────────┐
│ POST /predict/ │
│ {user_id, top_n}│
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Cold Start?     │
│ is_new_user()   │
└──┬──────────┬───┘
   │          │
   │ OUI      │ NON
   ▼          ▼
┌─────────┐ ┌──────────────────┐
│ Films   │ │ Charger modèle   │
│ Populaires│ │ depuis MLflow   │
└────┬────┘ └──────┬───────────┘
     │             │
     └──────┬──────┘
            │
            ▼
     ┌──────────────┐
     │ Générer      │
     │ Recommandations│
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │ Logger pour  │
     │ Monitoring   │
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │ Retourner    │
     │ JSON Response│
     └──────────────┘
```

## Flux de Monitoring

```
┌─────────────┐
│ Requête API │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Middleware      │
│ Prometheus      │
│ (Latence, Count)│
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Endpoint        │
│ (Training/Predict)│
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Métriques       │
│ Prometheus      │
│ /metrics        │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Grafana         │
│ Dashboards      │
└─────────────────┘
```

## Flux de Data Drift

```
┌─────────────┐
│ GET /monitoring/drift │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Charger Baseline│
│ (Statistiques)  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Calculer Stats  │
│ Actuelles       │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Comparer        │
│ (Threshold %)   │
└──┬──────────┬───┘
   │          │
   │ Dérive   │ Normal
   ▼          ▼
┌─────────┐ ┌─────────┐
│ Alert   │ │ OK      │
└─────────┘ └─────────┘
```

