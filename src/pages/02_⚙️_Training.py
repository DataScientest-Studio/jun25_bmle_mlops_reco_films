import streamlit as st
import time
from api_utils import api_request

st.set_page_config(page_title="Entraînement - Recommandation de Films", page_icon="⚙️", layout="wide")

st.title("⚙️ Gestion de l'Entraînement")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🚀 Lancer un nouvel entraînement")
    st.markdown("""
    L'entraînement va :
    1. Charger les dernières données depuis la base de données.
    2. Ré-entraîner les modèles (SVD, KNN).
    3. Évaluer les performances.
    4. Mettre à jour le modèle en production si les résultats sont meilleurs.
    """)
    
    force = st.checkbox("Forcer l'entraînement (même si un modèle récent existe)", value=False)
    
    if st.button("▶️ Démarrer l'Entraînement", type="primary", use_container_width=True):
        # Reset des états précédents
        if 'training_result' in st.session_state:
            del st.session_state['training_result']
        if 'idle_count' in st.session_state:
            del st.session_state['idle_count']
            
        with st.spinner("Démarrage du processus..."):
            data, error = api_request("POST", "/training/", json_data={"force": force})
        
        if error:
            st.error(f"❌ Erreur : {error}")
        else:
            st.success("✅ Entraînement lancé en arrière-plan !")
            st.session_state['training_started'] = True
            st.rerun()

with col2:
    st.subheader("🔍 Statut de l'entraînement")
    
    status_container = st.empty()
    
    # CAS 1 : Entraînement en cours (Polling actif)
    if st.session_state.get('training_started', False):
        
        # Conteneur stable pour éviter le clignotement
        progress_text = status_container.empty()
        
        # Boucle de polling
        while True:
            data, error = api_request("GET", "/training/status")
            
            if error:
                progress_text.error(f"Erreur de communication API : {error}")
                time.sleep(2)
                continue
            
            status = data.get("status", "unknown")
            message = data.get("message", "")
            
            if status == "training":
                # Reset idle counter si on détecte que ça tourne vraiment
                if 'idle_count' in st.session_state:
                    st.session_state['idle_count'] = 0
                # Affichage stable du message de progression
                progress_text.info(f"⏳ {message}")
                time.sleep(1)
                    
            elif status == "completed":
                progress_text.success(f"✅ {message}")
                # Sauvegarde du résultat
                st.session_state['training_result'] = {
                    "status": "success",
                    "message": message,
                    "metrics": data.get("metrics", {})
                }
                st.session_state['training_started'] = False
                st.rerun()
                
            elif status == "error":
                progress_text.error(f"❌ {message}")
                st.session_state['training_result'] = {
                    "status": "error",
                    "message": message
                }
                st.session_state['training_started'] = False
                st.rerun()
                
            else:
                # Cas IDLE ou autre inattendu pendant qu'on pense que ça tourne
                if 'idle_count' not in st.session_state:
                    st.session_state['idle_count'] = 0
                
                st.session_state['idle_count'] += 1
                
                if st.session_state['idle_count'] >= 5:
                    # Après 5 tentatives, on considère que l'entraînement est terminé
                    # On essaie de récupérer les métriques quand même
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
                    progress_text.info(f"⏳ Vérification du statut... ({st.session_state['idle_count']}/5)")
                    time.sleep(2)

    # CAS 2 : Résultat d'un entraînement terminé (stocké en session)
    elif 'training_result' in st.session_state:
        res = st.session_state['training_result']
        
        if res['status'] == "success":
            st.success(f"✅ {res['message']}")
            
            if res.get("metrics"):
                st.subheader("📊 Résultats de l'entraînement")
                
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
                        st.success("🏆 Meilleur modèle")
                
                with col_knn:
                    st.metric(
                        "KNN", 
                        f"{knn_rmse:.4f}" if knn_rmse else "N/A",
                        delta=f"{knn_rmse - best_rmse:.4f}" if (knn_rmse and best_rmse) else None,
                        delta_color="inverse"
                    )
                    if knn_rmse == best_rmse:
                        st.success("🏆 Meilleur modèle")
                
                with col_dummy:
                    st.metric(
                        "Baseline", 
                        f"{dummy_rmse:.4f}" if dummy_rmse else "N/A",
                        delta=f"{dummy_rmse - best_rmse:.4f}" if (dummy_rmse and best_rmse) else None,
                        delta_color="inverse"
                    )
                    if dummy_rmse == best_rmse:
                        st.success("🏆 Meilleur modèle")
                
                # Afficher toutes les métriques en détail
                with st.expander("Voir toutes les métriques"):
                    st.json(metrics)
                
            # Analyse du message pour savoir si le modèle a été mis à jour
            if "meilleur" in res['message'].lower() or "updated" in res['message'].lower():
                st.balloons()
                st.success("🌟 Nouveau modèle déployé !")
            else:
                st.info("ℹ️ Le modèle n'a pas été mis à jour (pas d'amélioration).")
                
        elif res['status'] == "error":
            st.error(f"❌ Échec : {res['message']}")
            
        if st.button("Effacer le résultat"):
            del st.session_state['training_result']
            st.rerun()

    # CAS 3 : État initial ou inconnu
    else:
        # Vérification ponctuelle au chargement de la page
        data, error = api_request("GET", "/training/status")
        
        if not error:
            status = data.get("status", "unknown")
            
            if status == "training":
                # On a raté le début, on se remet en mode polling
                st.session_state['training_started'] = True
                st.rerun()
            elif status == "completed":
                # C'est fini mais on n'a pas le résultat en session
                st.success(f"✅ Dernier entraînement : {data.get('message')}")
                if data.get("metrics"):
                    st.json(data["metrics"])
            elif status == "error":
                st.error(f"❌ Dernier entraînement échoué : {data.get('message')}")
            else:
                st.info("💤 Aucun entraînement en cours.")
