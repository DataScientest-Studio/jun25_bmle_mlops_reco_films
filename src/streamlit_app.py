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
st.caption("Projet MLOps - Recommandation de Films - 2025")
