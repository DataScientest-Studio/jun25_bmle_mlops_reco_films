import streamlit as st
import pandas as pd
from api_utils import api_request

st.set_page_config(page_title="Prédiction - Recommandation de Films", page_icon="🔮", layout="wide")

st.title("🔮 Obtenir des Recommandations")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("👤 Profil Utilisateur")
    user_id = st.number_input("ID Utilisateur", min_value=1, value=1, step=1, help="Entrez l'ID de l'utilisateur pour lequel vous voulez des recommandations.")
    top_n = st.slider("Nombre de films", min_value=1, max_value=20, value=5)
    
    st.info("""
    **💡 Astuce:**
    - **ID existant (ex: 1)** : Utilise le Collaborative Filtering (basé sur l'historique).
    - **Nouvel ID (ex: 999999)** : Utilise le Cold Start (basé sur la popularité).
    """)

    if st.button("🚀 Lancer la prédiction", type="primary", use_container_width=True):
        with st.spinner("Calcul des recommandations en cours..."):
            data, error = api_request("POST", "/predict/", json_data={
                "user_id": int(user_id),
                "top_n": int(top_n)
            }, timeout=60)
        
        if error:
            st.error(f"❌ Erreur : {error}")
        else:
            st.session_state['last_recommendations'] = data.get("recommendations", [])
            st.success("✅ Recommandations générées avec succès !")

with col2:
    st.subheader("🎬 Films Recommandés")
    
    if 'last_recommendations' in st.session_state and st.session_state['last_recommendations']:
        recommendations = st.session_state['last_recommendations']
        
        # Affichage sous forme de cartes ou liste
        for i, rec in enumerate(recommendations):
            with st.container():
                c1, c2 = st.columns([1, 4])
                with c1:
                    st.markdown(f"**#{i+1}**")
                    st.caption(f"Score: {rec['score']:.2f}")
                with c2:
                    st.markdown(f"**{rec['movie']}**")
                    st.progress(min(rec['score'] / 5.0, 1.0))
                st.divider()
                
        # Graphique récapitulatif
        st.subheader("📊 Comparaison des scores")
        df = pd.DataFrame(recommendations)
        st.bar_chart(df.set_index("movie")["score"])
        
    else:
        st.info("👈 Lancez une prédiction pour voir les résultats ici.")
