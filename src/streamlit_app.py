"""
Application Streamlit pour le système de recommandation de films
Interface utilisateur pour tester et visualiser les recommandations
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# Configuration
API_URL = st.sidebar.text_input("URL de l'API", value="http://localhost:8080")
st.set_page_config(page_title="Recommandation de Films", layout="wide")

st.title("Système de Recommandation de Films")
st.markdown("---")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choisir une page",
    ["Recommandations", "Entraînement", "Monitoring", "Data Drift", "Statistiques"]
)

# Fonction pour faire des requêtes API
def api_request(method, endpoint, json_data=None, params=None, timeout=30):
    """Fait une requête à l'API avec timeout configurable"""
    try:
        url = f"{API_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, params=params, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=json_data, timeout=timeout)
        else:
            return None, "Méthode non supportée"
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Erreur {response.status_code}: {response.text}"
    except requests.exceptions.Timeout:
        return None, f"Timeout: La requête a pris plus de {timeout} secondes. L'API est peut-être occupée ou la base de données est lente."
    except requests.exceptions.RequestException as e:
        return None, f"Erreur de connexion: {str(e)}"


# Page Recommandations
if page == "Recommandations":
    st.header("Obtenir des Recommandations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        user_id = st.number_input("ID Utilisateur", min_value=1, value=1, step=1)
        top_n = st.slider("Nombre de recommandations", min_value=1, max_value=20, value=5)
    
    with col2:
        st.info(f"""
        **Note:** 
        - Utilisez un ID élevé (ex: 999999) pour tester le **Cold Start**
        - Utilisez un ID existant (ex: 1) pour le **Collaborative Filtering**
        """)
    
    if st.button("Obtenir les Recommandations", type="primary"):
        with st.spinner("Génération des recommandations..."):
            data, error = api_request("POST", "/predict/", json_data={
                "user_id": int(user_id),
                "top_n": int(top_n)
            })
        
        if error:
            st.error(f"{error}")
        else:
            st.success("Recommandations générées avec succès")
            
            # Afficher les recommandations
            recommendations = data.get("recommendations", [])
            if recommendations:
                st.subheader(f"Top {len(recommendations)} Recommandations pour l'utilisateur {user_id}")
                
                # Créer un DataFrame pour l'affichage
                df = pd.DataFrame([
                    {
                        "Rang": i+1,
                        "Film": rec["movie"],
                        "Score": f"{rec['score']:.4f}"
                    }
                    for i, rec in enumerate(recommendations)
                ])
                
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Graphique des scores
                st.subheader("Scores des Recommandations")
                scores_df = pd.DataFrame({
                    "Film": [rec["movie"][:30] + "..." if len(rec["movie"]) > 30 else rec["movie"] for rec in recommendations],
                    "Score": [rec["score"] for rec in recommendations]
                })
                st.bar_chart(scores_df.set_index("Film"))
            else:
                st.warning("Aucune recommandation disponible")


# Page Entraînement
elif page == "Entraînement":
    st.header("Entraînement du Modèle")
    
    col1, col2 = st.columns(2)
    
    with col1:
        force = st.checkbox("Forcer l'entraînement", value=False)
        if st.button("Démarrer l'Entraînement", type="primary"):
            with st.spinner("Démarrage de l'entraînement..."):
                data, error = api_request("POST", "/training/", json_data={"force": force})
            
            if error:
                st.error(f"{error}")
            else:
                st.success("Entraînement démarré en arrière-plan")
                st.info("Utilisez le bouton ci-dessous pour vérifier le statut.")
    
    with col2:
        if st.button("Vérifier le Statut", type="secondary"):
            with st.spinner("Récupération du statut..."):
                data, error = api_request("GET", "/training/status")
            
            if error:
                st.error(f"{error}")
            else:
                status = data.get("status", "unknown")
                message = data.get("message", "")
                
                if status == "completed":
                    st.success(f"{message}")
                    st.json(data.get("metrics", {}))
                elif status == "training":
                    st.warning(f"{message}")
                elif status == "error":
                    st.error(f"{message}")
                else:
                    st.info(f"{message}")


# Page Monitoring
elif page == "Monitoring":
    st.header("Monitoring des Recommandations")
    
    days = st.slider("Période (jours)", min_value=1, max_value=30, value=7)
    
    if st.button("Rafraîchir les Statistiques", type="primary"):
        with st.spinner("Récupération des statistiques..."):
            data, error = api_request("GET", "/monitoring/recommendations", params={"days": days})
        
        if error:
            st.error(f"{error}")
        else:
            st.success("Statistiques recuperees")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Recommandations", data.get("total_recommendations", 0))
            
            with col2:
                st.metric("Diversité Moyenne", f"{data.get('avg_diversity', 0):.4f}")
            
            with col3:
                st.metric("Nouveauté Moyenne", f"{data.get('avg_novelty', 0):.4f}")
            
            with col4:
                st.metric("Score Moyen", f"{data.get('avg_score', 0):.4f}")
            
            # Méthodes utilisées
            methods = data.get("methods_used", {})
            if methods:
                st.subheader("Méthodes Utilisées")
                methods_df = pd.DataFrame(list(methods.items()), columns=["Méthode", "Nombre"])
                st.bar_chart(methods_df.set_index("Méthode"))


# Page Data Drift
elif page == "Data Drift":
    st.header("Détection de Data Drift")
    
    col1, col2 = st.columns(2)
    
    with col1:
        threshold = st.slider("Seuil de détection (%)", min_value=1, max_value=50, value=10)
        
        if st.button("Vérifier le Drift", type="primary"):
            with st.spinner("Analyse du drift... (cela peut prendre jusqu'à 30 secondes)"):
                data, error = api_request("GET", "/monitoring/drift", params={"threshold_pct": threshold}, timeout=60)
                
                if error:
                    st.error(f"{error}")
                else:
                    drift_detected = data.get("drift_detected", False)
                    
                    if drift_detected:
                        st.error("DRIFT DETECTE")
                    else:
                        st.success("Pas de drift detecte")
                    
                    # Afficher les détails
                    drift_details = data.get("drift_details", {})
                    if drift_details:
                        st.subheader("Détails du Drift")
                        for metric, details in drift_details.items():
                            status = details.get("status", "unknown")
                            change_pct = details.get("change_pct", 0)
                            baseline = details.get("baseline", 0)
                            current = details.get("current", 0)
                            
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric(f"{metric} (Baseline)", f"{baseline:.2f}")
                            with col_b:
                                st.metric(f"{metric} (Actuel)", f"{current:.2f}")
                            with col_c:
                                st.metric(f"Changement", f"{change_pct:.2f}%", delta=None)
                                st.write(f"{status}")
    
    with col2:
        if st.button("Créer une Baseline", type="secondary"):
            with st.spinner("Création de la baseline... (cela peut prendre jusqu'à 30 secondes)"):
                data, error = api_request("POST", "/monitoring/drift/baseline", timeout=60)
                
                if error:
                    st.error(f"{error}")
                else:
                    st.success("Baseline creee avec succes")
                    st.json(data)


# Page Statistiques
elif page == "Statistiques":
    st.header("Statistiques des Donnees")
    
    days = st.number_input("Période (jours, laisser vide pour toutes les données)", 
                          min_value=1, value=None, step=1)
    
    if st.button("Rafraîchir les Statistiques", type="primary"):
        params = {"days": days} if days else None
        with st.spinner("Récupération des statistiques... (cela peut prendre jusqu'à 30 secondes)"):
            data, error = api_request("GET", "/monitoring/stats", params=params, timeout=60)
        
        if error:
            st.error(f"{error}")
        else:
            st.success("Statistiques recuperees")
            
            stats = data.get("statistics", {})
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Utilisateurs", f"{stats.get('num_users', 0):,}")
            
            with col2:
                st.metric("Films", f"{stats.get('num_movies', 0):,}")
            
            with col3:
                st.metric("Ratings", f"{stats.get('num_ratings', 0):,}")
            
            with col4:
                st.metric("Note Moyenne", f"{stats.get('avg_rating', 0):.2f}")
            
            # Graphique de distribution
            st.subheader("Distribution des Notes")
            st.info(f"Min: {stats.get('min_rating', 0)} | Max: {stats.get('max_rating', 0)} | Std: {stats.get('std_rating', 0):.2f}")


# Footer
st.markdown("---")
st.markdown(f"Derniere mise a jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

