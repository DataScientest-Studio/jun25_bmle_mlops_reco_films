import streamlit as st
import graphviz

st.set_page_config(
    page_title="Rapport de Projet - MLOps",
    layout="wide",
    page_icon="📝"
)

st.title("📝 Rapport Complet du Projet MLOps")
st.markdown("### Architecture, Analyse et Perspectives")

st.markdown("---")

# ============================================================================
# 1. ARCHITECTURE DU SYSTÈME
# ============================================================================

st.header("🏗️ Architecture du Système")

st.markdown("""
Le système repose sur une architecture **microservices** orchestrée par Docker Compose. 
Chaque composant a une responsabilité unique et communique avec les autres via des interfaces définies (API REST, Base de données, Stockage S3).
""")

# Diagramme d'architecture avec Graphviz
graph = graphviz.Digraph()
graph.attr(rankdir='TB', size='10')

# Styles
graph.attr('node', shape='box', style='filled', fillcolor='lightblue', fontname='Helvetica')
graph.attr('edge', fontname='Helvetica', fontsize='10')

# Clusters (Groupes de services)
with graph.subgraph(name='cluster_data') as c:
    c.attr(label='Data Layer', color='grey', style='dashed')
    c.node('PostgreSQL', 'PostgreSQL\n(DB: 5432)', fillcolor='#e1f5fe')
    c.node('MinIO', 'MinIO\n(S3: 9000)', fillcolor='#e1f5fe')

with graph.subgraph(name='cluster_ml') as c:
    c.attr(label='ML & Processing', color='grey', style='dashed')
    c.node('MLflow', 'MLflow\n(Tracking: 5000)', fillcolor='#fff9c4')
    c.node('API', 'FastAPI\n(Backend: 8080)', fillcolor='#c8e6c9')
    c.node('Airflow', 'Airflow\n(Orchestration: 8081)', fillcolor='#fff9c4')

with graph.subgraph(name='cluster_monitoring') as c:
    c.attr(label='Monitoring', color='grey', style='dashed')
    c.node('Prometheus', 'Prometheus\n(Metrics: 9090)', fillcolor='#ffccbc')
    c.node('Grafana', 'Grafana\n(Viz: 3001)', fillcolor='#ffccbc')

with graph.subgraph(name='cluster_ui') as c:
    c.attr(label='User Interface', color='grey', style='dashed')
    c.node('Streamlit', 'Streamlit\n(Frontend: 8501)', fillcolor='#d1c4e9')

# Connexions
graph.edge('Streamlit', 'API', label='HTTP Requests')
graph.edge('API', 'PostgreSQL', label='SQL Queries')
graph.edge('API', 'MLflow', label='Log Metrics')
graph.edge('API', 'MinIO', label='Load Models')
graph.edge('Airflow', 'API', label='Trigger Training')
graph.edge('MLflow', 'PostgreSQL', label='Backend Store')
graph.edge('MLflow', 'MinIO', label='Artifact Store')
graph.edge('Prometheus', 'API', label='Scrape /metrics')
graph.edge('Grafana', 'Prometheus', label='Query Data')

st.graphviz_chart(graph)

st.markdown("### 🔍 Détail des Composants")

with st.expander("🟦 Couche Data (Stockage)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **PostgreSQL (Base de Données Relationnelle)**
        - **Fonction** : Système de gestion de base de données relationnelle (SGBDR) principal.
        - **Données stockées** : 
            - Données métiers : Films, utilisateurs, évaluations, tags.
            - Données applicatives : Métadonnées Airflow, logs applicatifs.
        - **Interactions** : Source de vérité pour l'API (lecture/écriture) et source de données pour le pipeline d'entraînement (extraction).
        """)
    with col2:
        st.markdown("""
        **MinIO (Object Storage S3-Compatible)**
        - **Fonction** : Solution de stockage d'objets haute performance compatible S3.
        - **Données stockées** : 
            - Artefacts ML : Modèles sérialisés (`.pkl`), métriques.
            - Rapports : Fichiers HTML de détection de drift (Evidently).
        - **Interactions** : Backend de stockage pour MLflow Artifacts et DVC.
        """)

with st.expander("🟩 Couche Backend & ML (Traitement)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **FastAPI (API REST)**
        - **Fonction** : Interface de programmation applicative asynchrone.
        - **Responsabilités** : 
            - Point d'entrée unique pour toutes les requêtes clients.
            - Orchestration des logiques métiers (Inférence, Cold Start).
            - Exposition des métriques techniques via middleware Prometheus.
        - **Caractéristiques** : Haute performance, validation Pydantic, documentation OpenAPI automatique.
        """)
        st.markdown("""
        **MLflow (ML Lifecycle Management)**
        - **Fonction** : Plateforme de gestion du cycle de vie des modèles ML.
        - **Responsabilités** : 
            - Experiment Tracking : Enregistrement des hyperparamètres et métriques.
            - Model Registry : Gestion des versions et des états (Staging, Production).
            - Centralisation des résultats d'entraînement.
        """)
    with col2:
        st.markdown("""
        **Airflow (Orchestration de Workflow)**
        - **Fonction** : Plateforme de planification et de surveillance des workflows.
        - **Responsabilités** : 
            - Planification des tâches récurrentes (DAGs).
            - Gestion des dépendances entre les tâches (ETL, Entraînement).
            - Surveillance de l'état de santé du pipeline et reprises sur erreur (Retries).
        """)

with st.expander("🟧 Couche Monitoring (Observabilité)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Prometheus (Time Series Database)**
        - **Fonction** : Système de monitoring et d'alerting basé sur des séries temporelles.
        - **Responsabilités** : 
            - Scraping périodique des métriques exposées par l'API.
            - Stockage efficace des métriques techniques et métiers.
        """)
    with col2:
        st.markdown("""
        **Grafana (Visualisation & Analytics)**
        - **Fonction** : Plateforme d'analyse et de visualisation interactive.
        - **Responsabilités** : 
            - Agrégation des données Prometheus dans des tableaux de bord.
            - Visualisation en temps réel de la santé du système (Latence, Débit, Erreurs).
            - Gestion des règles d'alerting.
        """)

with st.expander("🟪 Couche Frontend (Interface Utilisateur)", expanded=True):
    st.markdown("""
    **Streamlit (Web Application)**
    - **Fonction** : Framework open-source pour les applications de Data Science.
    - **Responsabilités** : 
        - Interface graphique pour l'interaction utilisateur.
        - Visualisation des résultats de recommandation.
        - Démonstration des capacités du système (Entraînement, Monitoring).
    """)

st.markdown("---")

# ============================================================================
# 2. FLUX DE DONNÉES & MÉTRIQUES
# ============================================================================

st.header("🔄 Flux de Données & Métriques")

st.markdown("""
Ce diagramme illustre le cycle de vie de la donnée, de son ingestion brute jusqu'aux métriques de monitoring, en passant par la création du modèle.
""")

# Diagramme de flux de données
data_graph = graphviz.Digraph()
data_graph.attr(rankdir='LR', size='12')

# Styles des noeuds
data_graph.attr('node', shape='ellipse', style='filled', fontname='Helvetica')
data_graph.node('CSV', 'Fichiers CSV\n(MovieLens)', fillcolor='#e0e0e0', shape='note')
data_graph.node('DB', 'PostgreSQL\n(Données)', fillcolor='#e1f5fe', shape='cylinder')
data_graph.node('Pipeline', 'Pipeline\nEntraînement', fillcolor='#c8e6c9', shape='box')
data_graph.node('Model', 'Modèle\n(.pkl)', fillcolor='#fff9c4', shape='component')
data_graph.node('MinIO', 'MinIO\n(Stockage)', fillcolor='#e1f5fe', shape='cylinder')
data_graph.node('MLflow', 'MLflow\n(Tracking)', fillcolor='#fff9c4', shape='box')
data_graph.node('API', 'API\n(Inférence)', fillcolor='#c8e6c9', shape='box')
data_graph.node('Prometheus', 'Prometheus\n(Métriques)', fillcolor='#ffccbc', shape='cylinder')
data_graph.node('Grafana', 'Grafana\n(Dashboards)', fillcolor='#ffccbc', shape='box')
data_graph.node('Drift', 'Détection Drift\n(Evidently)', fillcolor='#ffccbc', shape='box')
data_graph.node('Report', 'Rapport Drift\n(.html)', fillcolor='#e1f5fe', shape='note')
data_graph.node('Airflow', 'Airflow\n(Scheduler)', fillcolor='#fff9c4', shape='box')

# Flux de Données (Bleu)
data_graph.edge('CSV', 'DB', label='Import', color='blue', fontcolor='blue')
data_graph.edge('DB', 'Pipeline', label='Load Ratings', color='blue', fontcolor='blue')
data_graph.edge('DB', 'API', label='Read History', color='blue', fontcolor='blue')
data_graph.edge('DB', 'Drift', label='Current Data', color='blue', fontcolor='blue')
data_graph.edge('MinIO', 'Drift', label='Ref Data', color='blue', fontcolor='blue')

# Flux de Modèles (Vert)
data_graph.edge('Airflow', 'API', label='Trigger Train', color='green', fontcolor='green')
data_graph.edge('Pipeline', 'Model', label='Train', color='green', fontcolor='green')
data_graph.edge('Model', 'MinIO', label='Save Artifact', color='green', fontcolor='green')
data_graph.edge('MinIO', 'API', label='Load Model', color='green', fontcolor='green')

# Flux de Métriques (Rouge)
data_graph.edge('Pipeline', 'MLflow', label='Log RMSE/MAE', color='red', fontcolor='red')
data_graph.edge('API', 'Prometheus', label='Expose /metrics', color='red', fontcolor='red')
data_graph.edge('Drift', 'Prometheus', label='Drift Metrics', color='red', fontcolor='red')
data_graph.edge('Prometheus', 'Grafana', label='Query', color='red', fontcolor='red')
data_graph.edge('Drift', 'Report', label='Generate', color='red', fontcolor='red')
data_graph.edge('Report', 'MinIO', label='Archive', color='green', fontcolor='green')

st.graphviz_chart(data_graph)

st.markdown("""
**Légende des Flux :**
- 🔵 **Données** : Mouvement des données brutes et transformées.
- 🟢 **Modèles & Orchestration** : Cycle de vie des modèles et déclenchement automatique.
- 🔴 **Métriques & Monitoring** : Envoi des indicateurs de performance, de santé et de dérive.

**Détail du Monitoring et de l'Observabilité :**
- **Airflow** : Orchestre le ré-entraînement quotidien en appelant l'API.
- **Prometheus** : Collecte les métriques techniques (latence, erreurs) et métier (nombre de recommandations) en temps réel.
- **Grafana** : Interroge Prometheus pour visualiser ces métriques sous forme de tableaux de bord interactifs.
- **Evidently (Drift)** : Compare périodiquement les données de production ("Current Data") avec les données d'entraînement ("Ref Data") stockées dans MinIO.
- **Rapports** : Si une dérive est détectée, un rapport HTML détaillé est généré et archivé dans MinIO pour analyse.
""")

st.markdown("---")

# ============================================================================
# 3. SCÉNARIOS D'UTILISATION
# ============================================================================

st.header("📋 Scénarios d'Utilisation")

tab1, tab2, tab3 = st.tabs(["🚀 Entraînement", "🎯 Prédiction", "📊 Monitoring"])

with tab1:
    st.markdown("Deux modes de déclenchement sont possibles :")
    
    col_manual, col_auto = st.columns(2)
    
    with col_manual:
        st.markdown("#### 👤 Déclenchement Manuel")
        st.markdown("*Via l'interface Streamlit (Bouton)*")
        st.markdown("""
        1. **Action** : L'utilisateur clique sur "Lancer l'entraînement".
        2. **API Call** : Requête `POST /training/` envoyée à l'API.
        3. **Execution** : L'API lance l'entraînement en tâche de fond (Background Task).
        4. **Feedback** : L'utilisateur reçoit une notification de succès immédiate.
        """)
        st.warning("⚠️ Ce mode n'inclut PAS la génération de nouvelles données.")

    with col_auto:
        st.markdown("#### 🤖 Déclenchement Automatique")
        st.markdown("*Via l'orchestrateur Airflow (Quotidien)*")
        st.markdown("""
        1. **Schedule** : Le DAG se lance tous les jours à 02h00.
        2. **Data Gen** : Appel `POST /generate-ratings` (Simulation de 100 nouveaux votes).
        3. **Training** : Appel `POST /training/` (Ré-entraînement complet).
        4. **Monitoring** : Si échec, Airflow envoie une alerte et retry.
        """)
        st.success("✅ Ce mode assure que le modèle apprend en continu sur des données fraîches.")

    st.markdown("#### ⚙️ Pipeline Commun (Exécuté par l'API)")
    st.markdown("""
    Une fois déclenché (manuellement ou automatiquement), le processus est identique :
    1. **Data Loading** : Chargement des données depuis PostgreSQL.
    2. **Training** : Entraînement parallèle (SVD, KNN, Baseline).
    3. **Evaluation** : Cross-Validation (RMSE).
    4. **Tracking** : Log dans MLflow.
    5. **Deployment** : Sauvegarde dans MinIO si le modèle est meilleur.
    """)

with tab2:
    st.subheader("Flux de Prédiction (Inférence)")
    st.markdown("""
    L'API gère les demandes de recommandation en temps réel.
    
    1. **Request** : L'utilisateur demande des recommandations via **Streamlit**.
    2. **User Check** : L'API vérifie si l'utilisateur existe dans **PostgreSQL**.
    3. **Routing** :
        - **Utilisateur Existant** : Chargement du modèle **SVD** depuis le cache/disque. Inférence sur les films non vus.
        - **Nouvel Utilisateur (Cold Start)** : Appel au module `cold_start.py`. Recommandation basée sur la popularité et les genres.
    4. **Filtering** : Tri des scores et sélection du Top-N.
    5. **Response** : Renvoi de la liste des films avec titres et scores.
    """)
    st.success("✅ Le système gère nativement le problème du 'Cold Start'.")

with tab3:
    st.subheader("Boucle de Monitoring")
    st.markdown("""
    L'observabilité est assurée en continu.
    
    1. **Instrumentation** : L'API expose des métriques techniques et métier sur `/metrics`.
    2. **Collection** : **Prometheus** scrape ces métriques toutes les 15s.
    3. **Visualization** : **Grafana** affiche des dashboards (Latence, Erreurs, Drift).
    4. **Drift Detection** : Un endpoint spécifique calcule le drift statistique (Kolmogorov-Smirnov) et génère des rapports **Evidently**.
    """)

st.markdown("---")

# ============================================================================
# 4. ANALYSE DU PROJET
# ============================================================================

st.header("📝 Analyse Détaillée")

with st.expander("🤖 Choix des Modèles"):
    st.markdown("""
    Nous avons implémenté et comparé plusieurs approches :
    
    - **SVD (Singular Value Decomposition)** : Méthode de factorisation matricielle. Généralement la plus performante pour capturer les motifs latents. C'est notre modèle "champion" par défaut.
    - **KNNBasic (K-Nearest Neighbors)** : Filtrage collaboratif basé sur la similarité (User-User ou Item-Item). Utile pour l'explicabilité ("Parce que vous avez aimé X...").
    - **NormalPredictor** : Baseline aléatoire suivant la distribution des notes. Sert de point de référence plancher.
    """)

with st.expander("✨ Pratiques MLOps Implémentées"):
    st.markdown("""
    Ce projet respecte les standards MLOps :
    
    - **Reproductibilité** : Environnement Dockerisé, versions fixées.
    - **Versioning** : Code (Git), Données (DVC - *structure prête*), Modèles (MLflow).
    - **Automatisation** : Pipeline CI/CD (simulé via Airflow pour le CD du modèle).
    - **Monitoring Continu** : Feedback loop sur la qualité des données et du modèle.
    - **Scalabilité** : Architecture découplée permettant de scaler l'API indépendamment de l'entraînement.
    """)

st.markdown("---")

# ============================================================================
# 5. PERSPECTIVES D'ÉVOLUTION
# ============================================================================

st.header("🔮 Perspectives d'Évolution Future")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🚀 Court Terme")
    st.markdown("""
    - **Tests A/B en Production** : Implémenter un vrai routing de trafic pour comparer deux modèles sur des utilisateurs réels.
    - **Enrichissement des Données** : Utiliser le NLP sur les synopsis de films ou les tags pour améliorer le modèle (Hybrid Filtering).
    - **Optimisation des Hyperparamètres** : Intégrer `Optuna` ou `Hyperopt` dans le pipeline d'entraînement Airflow.
    - **Pipeline CI/CD Complet** : Automatiser les tests unitaires (`pytest`) et le build Docker à chaque push (GitHub Actions / GitLab CI).
    """)

with col2:
    st.subheader("🌟 Long Terme")
    st.markdown("""
    - **Scalabilité Kubernetes** : Migrer de Docker Compose vers K8s pour l'orchestration de conteneurs en production.
    - **Feature Store** : Mettre en place un Feature Store (ex: Feast) pour servir les features en temps réel avec faible latence.
    - **Modèles Deep Learning** : Explorer des architectures neuronales (NeuralCF, Autoencoders) pour capturer des relations non-linéaires complexes.
    """)

st.markdown("---")
st.caption("Rapport généré automatiquement par l'application MLOps - 2025")
