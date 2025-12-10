import streamlit as st
import time
from api_utils import api_request

st.set_page_config(page_title="Entraînement - Recommandation de Films", layout="wide")

st.title("Gestion de l'Entraînement")
st.markdown("---")

with st.container():
    st.info("**Orchestration** : L'entraînement est planifié automatiquement chaque nuit via **Apache Airflow**.")
    st.markdown("[Accéder à l'interface Airflow](http://localhost:8081) (admin/admin)")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Lancer un nouvel entraînement manuellement")
    st.markdown("""
    L'entraînement va :
    1. Charger les dernières données depuis la base de données.
    2. Ré-entraîner les modèles (SVD, KNN).
    3. Évaluer les performances.
    4. Mettre à jour le modèle en production si les résultats sont meilleurs.
    """)
    
    force = st.checkbox("Forcer l'entraînement (même si un modèle récent existe)", value=False)
    
    if st.button("Démarrer l'Entraînement", type="primary", use_container_width=True):
        # Reset des états précédents
        if 'training_result' in st.session_state:
            del st.session_state['training_result']
        if 'idle_count' in st.session_state:
            del st.session_state['idle_count']
            
        with st.spinner("Démarrage du processus..."):
            data, error = api_request("POST", "/training/", json_data={"force": force})
        
        if error:
            st.error(f"Erreur : {error}")
        else:
            st.success("Entraînement lancé en arrière-plan")
            st.session_state['training_started'] = True
            st.rerun()

with col2:
    st.subheader("Statut de l'entraînement")
    
    status_container = st.empty()
    
    if st.session_state.get('training_started', False):
        progress_text = status_container.empty()
        
        while True:
            data, error = api_request("GET", "/training/status")
            
            if error:
                progress_text.error(f"Erreur de communication API : {error}")
                time.sleep(2)
                continue
            
            status = data.get("status", "unknown")
            message = data.get("message", "")
            
            if status == "training":
                if 'idle_count' in st.session_state:
                    st.session_state['idle_count'] = 0
                progress_text.info(message)
                time.sleep(1)
                    
            elif status == "completed":
                progress_text.success(message)
                st.session_state['training_result'] = {
                    "status": "success",
                    "message": message,
                    "metrics": data.get("metrics", {})
                }
                st.session_state['training_started'] = False
                st.rerun()
                
            elif status == "error":
                progress_text.error(message)
                st.session_state['training_result'] = {
                    "status": "error",
                    "message": message
                }
                st.session_state['training_started'] = False
                st.rerun()
                
            else:
                if 'idle_count' not in st.session_state:
                    st.session_state['idle_count'] = 0
                
                st.session_state['idle_count'] += 1
                
                if st.session_state['idle_count'] >= 5:
                    final_message = data.get("message", "Entraînement terminé")
                    final_metrics = data.get("metrics", {})
                    
                    st.session_state['training_result'] = {
                        "status": "success",
                        "message": final_message,
                        "metrics": final_metrics
                    }
                    st.session_state['training_started'] = False
                    st.session_state['idle_count'] = 0
                    st.rerun()
                else:
                    progress_text.info(f"Vérification du statut... ({st.session_state['idle_count']}/5)")
                    time.sleep(2)

    elif 'training_result' in st.session_state:
        res = st.session_state['training_result']
        
        if res['status'] == "success":
            st.success(res['message'])
            
            if res.get("metrics"):
                st.subheader("Résultats de l'entraînement")
                
                # Extraire les métriques RMSE
                metrics = res["metrics"]
                svd_rmse = metrics.get("svd_rmse")
                knn_rmse = metrics.get("knn_rmse")
                dummy_rmse = metrics.get("dummy_rmse")
                best_rmse = metrics.get("best_rmse")
                
                # Affichage en colonnes
                col_svd, col_knn, col_dummy = st.columns(3)
                
                with col_svd:
                    st.metric(
                        "SVD", 
                        f"{svd_rmse:.4f}" if svd_rmse else "N/A",
                        delta=f"{svd_rmse - best_rmse:.4f}" if (svd_rmse and best_rmse) else None,
                        delta_color="inverse"
                    )
                    if svd_rmse == best_rmse:
                        st.success("Meilleur modèle")
                
                with col_knn:
                    st.metric(
                        "KNN", 
                        f"{knn_rmse:.4f}" if knn_rmse else "N/A",
                        delta=f"{knn_rmse - best_rmse:.4f}" if (knn_rmse and best_rmse) else None,
                        delta_color="inverse"
                    )
                    if knn_rmse == best_rmse:
                        st.success("Meilleur modèle")
                
                with col_dummy:
                    st.metric(
                        "Baseline", 
                        f"{dummy_rmse:.4f}" if dummy_rmse else "N/A",
                        delta=f"{dummy_rmse - best_rmse:.4f}" if (dummy_rmse and best_rmse) else None,
                        delta_color="inverse"
                    )
                    if dummy_rmse == best_rmse:
                        st.success("Meilleur modèle")
                
                with st.expander("Voir toutes les métriques"):
                    st.json(metrics)
                
            if "meilleur" in res['message'].lower() or "updated" in res['message'].lower():
                st.balloons()
                st.success("Nouveau modèle déployé")
            else:
                st.info("Le modèle n'a pas été mis à jour (pas d'amélioration).")
                
        elif res['status'] == "error":
            st.error(f"Échec : {res['message']}")
            
        if st.button("Effacer le résultat"):
            del st.session_state['training_result']
            st.rerun()

    else:
        data, error = api_request("GET", "/training/status")
        
        if not error:
            status = data.get("status", "unknown")
            
            if status == "training":
                st.session_state['training_started'] = True
                st.rerun()
            elif status == "completed":
                st.success(f"Dernier entraînement : {data.get('message')}")
                
                if data.get("metrics"):
                    st.subheader("Résultats de l'entraînement")
                    
                    # Extraire les métriques RMSE
                    metrics = data["metrics"]
                    svd_rmse = metrics.get("svd_rmse")
                    knn_rmse = metrics.get("knn_rmse")
                    dummy_rmse = metrics.get("dummy_rmse")
                    best_rmse = metrics.get("best_rmse")
                    
                    # Affichage en colonnes
                    col_svd, col_knn, col_dummy = st.columns(3)
                    
                    with col_svd:
                        st.metric(
                            "SVD", 
                            f"{svd_rmse:.4f}" if svd_rmse else "N/A",
                            delta=f"{svd_rmse - best_rmse:.4f}" if (svd_rmse and best_rmse) else None,
                            delta_color="inverse"
                        )
                        if svd_rmse == best_rmse:
                            st.success("Meilleur modèle")
                    
                    with col_knn:
                        st.metric(
                            "KNN", 
                            f"{knn_rmse:.4f}" if knn_rmse else "N/A",
                            delta=f"{knn_rmse - best_rmse:.4f}" if (knn_rmse and best_rmse) else None,
                            delta_color="inverse"
                        )
                        if knn_rmse == best_rmse:
                            st.success("Meilleur modèle")
                    
                    with col_dummy:
                        st.metric(
                            "Baseline", 
                            f"{dummy_rmse:.4f}" if dummy_rmse else "N/A",
                            delta=f"{dummy_rmse - best_rmse:.4f}" if (dummy_rmse and best_rmse) else None,
                            delta_color="inverse"
                        )
                        if dummy_rmse == best_rmse:
                            st.success("Meilleur modèle")
                    
                    with st.expander("Voir toutes les métriques"):
                        st.json(metrics)
                        
            elif status == "error":
                st.error(f"Dernier entraînement échoué : {data.get('message')}")
            else:
                st.info("Aucun entraînement en cours.")
