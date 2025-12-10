import streamlit as st
import os

st.set_page_config(
    page_title="Accueil - MLOps Recommandation",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Système de Recommandation de Films MLOps")

st.markdown("""
### Bienvenue sur le tableau de bord MLOps

Cette application permet d'interagir avec le système de recommandation de films.
Utilisez le menu latéral pour naviguer entre les différentes fonctionnalités :

- **Prédiction** : Obtenez des recommandations de films personnalisées pour un utilisateur.
- **Entraînement** : Lancez le ré-entraînement du modèle sur les nouvelles données et suivez sa progression.
- **Monitoring** : Surveillez la qualité des recommandations et détectez le "Data Drift" (dérive des données).

---
### État du Système
""")

from api_utils import api_request
data, error = api_request("GET", "/health", timeout=2)

col1, col2, col3 = st.columns(3)

with col1:
    if error:
        st.error("API Déconnectée")
        st.caption(f"Erreur: {error}")
    else:
        st.success("API Connectée")
        st.caption(f"Version: {data.get('version', 'unknown')}")

with col2:
    st.info("Environnement Docker")
    st.caption("Conteneurs actifs")

with col3:
    st.warning("Base de Données")
    st.caption("PostgreSQL")

st.markdown("---")

st.subheader("🔗 Accès aux Services")

st.markdown("""
Accédez directement aux différents modules et interfaces du système :
""")

# API Endpoints
col_api1, col_api2 = st.columns(2)

with col_api1:
    st.markdown("#### 📡 API REST")
    st.markdown(f"""
    - [📚 Documentation API (Swagger)](http://localhost:8080/docs)
    - [❤️ Health Check](http://localhost:8080/health)
    - [📊 Métriques Prometheus](http://localhost:8080/metrics)
    """)

with col_api2:
    st.markdown("#### 🛠️ Outils MLOps")
    st.markdown(f"""
    - [🧪 MLflow Tracking](http://localhost:5000)
    - [📅 Apache Airflow](http://localhost:8081)
    - [📊 Grafana Dashboards](http://localhost:3001)
    - [🔍 Prometheus](http://localhost:9090)
    """)

# Database & Storage
col_db1, col_db2 = st.columns(2)

with col_db1:
    st.markdown("#### 💾 Base de Données")
    st.markdown(f"""
    - [🐘 pgAdmin](http://localhost:5050)
    """)

with col_db2:
    st.markdown("#### 📦 Stockage")
    st.markdown(f"""
    - [🗄️ MinIO Console](http://localhost:9001)
    """)

st.markdown("---")
st.caption("Projet MLOps - Recommandation de Films - 2025")
