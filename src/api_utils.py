import streamlit as st
import requests
import os

# Configuration
# On récupère l'URL de l'API depuis les secrets Streamlit ou l'environnement, sinon localhost
API_URL = os.getenv("API_URL", "http://api:8000")

def get_api_url():
    """Récupère l'URL de l'API configurée dans la session ou par défaut."""
    if "api_url" in st.session_state:
        return st.session_state.api_url
    return API_URL

def api_request(method, endpoint, json_data=None, params=None, timeout=30):
    """
    Fait une requête à l'API avec gestion des erreurs et timeout.
    
    Args:
        method (str): "GET" ou "POST"
        endpoint (str): Endpoint de l'API (ex: "/training/")
        json_data (dict): Données JSON pour POST
        params (dict): Paramètres URL pour GET
        timeout (int): Timeout en secondes
        
    Returns:
        tuple: (data, error_message)
    """
    base_url = get_api_url()
    # Nettoyage des slashes pour éviter //
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
        
    url = f"{base_url}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=json_data, timeout=timeout)
        else:
            return None, "Méthode non supportée"
        
        if response.status_code == 200:
            return response.json(), None
        else:
            try:
                err_msg = response.json().get("detail", response.text)
            except:
                err_msg = response.text
            return None, f"Erreur {response.status_code}: {err_msg}"
            
    except requests.exceptions.Timeout:
        return None, f"Timeout: La requête a pris plus de {timeout} secondes."
    except requests.exceptions.ConnectionError:
        return None, f"Impossible de se connecter à l'API ({url}). Vérifiez qu'elle est bien lancée."
    except requests.exceptions.RequestException as e:
        return None, f"Erreur de connexion: {str(e)}"
