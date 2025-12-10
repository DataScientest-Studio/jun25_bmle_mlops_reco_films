import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
from api_utils import api_request

st.set_page_config(page_title="Monitoring - Recommandation de Films", layout="wide")

st.title("Monitoring & Observabilité")

tab1, tab2, tab3 = st.tabs(["Dashboard Grafana", "Qualité des Recommandations", "Data Drift"])

with tab1:
    st.header("Dashboard Grafana")
    grafana_url = "http://localhost:3001/d/69030c37-8da9-4eef-b248-ff47fc912e4a/api-metrics-dashboard?orgId=1&from=now-6h&to=now&timezone=browser&refresh=10s&kiosk"
    components.iframe(src=grafana_url, height=600, scrolling=True)

with tab2:
    st.header("Qualité des Recommandations")
    days = st.slider("Période d'analyse (jours)", 1, 30, 7)
    
    if st.button("Rafraîchir les métriques"):
        with st.spinner("Chargement..."):
            data, error = api_request("GET", "/monitoring/recommendations", params={"days": days})
            
            if error:
                st.error(error)
            else:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Recommandations", data.get("total_recommendations", 0))
                c2.metric("Diversité", f"{data.get('avg_diversity', 0):.3f}")
                c3.metric("Nouveauté", f"{data.get('avg_novelty', 0):.3f}")
                c4.metric("Score Moyen", f"{data.get('avg_score', 0):.2f}")
                
                if "methods_used" in data:
                    st.subheader("Méthodes utilisées")
                    df_methods = pd.DataFrame(list(data["methods_used"].items()), columns=["Méthode", "Nombre"])
                    fig = px.pie(df_methods, values="Nombre", names="Méthode", title="Répartition des méthodes de recommandation")
                    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Détection de Data Drift")
    st.markdown("Compare les statistiques actuelles des données avec la baseline (référence).")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        threshold = st.slider("Seuil d'alerte (%)", 1, 50, 10)
        if st.button("Analyser le Drift", type="primary"):
            with st.spinner("Analyse en cours..."):
                data, error = api_request("GET", "/monitoring/drift", params={"threshold_pct": threshold})
                
                if error:
                    st.error(error)
                else:
                    drift = data.get("drift_detected", False)
                    if drift:
                        st.error("DRIFT DÉTECTÉ : Les données ont changé significativement.")
                    else:
                        st.success("Aucun drift significatif détecté.")
                    
                    details = data.get("drift_details", {})
                    if details:
                        rows = []
                        for metric, values in details.items():
                            rows.append({
                                "Métrique": metric,
                                "Baseline": values["baseline"],
                                "Actuel": values["current"],
                                "Variation (%)": f"{values['change_pct']:.2f}%",
                                "Statut": values["status"]
                            })
                        st.dataframe(pd.DataFrame(rows), use_container_width=True)

    with col2:
        st.info("Si les données ont changé légitimement, mettez à jour la baseline.")
        if st.button("Mettre à jour la Baseline"):
            with st.spinner("Mise à jour..."):
                data, error = api_request("POST", "/monitoring/drift/baseline")
                if error:
                    st.error(error)
                else:
                    st.success("Nouvelle baseline enregistrée")
