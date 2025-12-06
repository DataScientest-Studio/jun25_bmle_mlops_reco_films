.PHONY: help build up down logs restart clean test lint train predict streamlit-rebuild

# Couleurs pour l'aide
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "${YELLOW}%-20s${NC} %s\n", $$1, $$2}'

# ============================================================================
# 🐳 Docker Management
# ============================================================================

build: ## Construit tous les conteneurs
	docker compose build

up: ## Lance tous les conteneurs en tâche de fond (detached)
	docker compose up -d

down: ## Arrête et supprime tous les conteneurs
	docker compose down

restart: down up ## Redémarre tous les conteneurs

logs: ## Affiche les logs de tous les conteneurs en temps réel
	docker compose logs -f

ps: ## Affiche l'état des conteneurs
	docker compose ps

# ============================================================================
# 🛠️ Development & Tests
# ============================================================================

test: ## Lance les tests unitaires via pytest (dans le conteneur API)
	docker compose run --rm api pytest tests/

lint: ## Lance le linter (flake8) sur le code source
	docker compose run --rm api flake8 src/

clean: ## Nettoie les fichiers temporaires (__pycache__, .pytest_cache)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

# ============================================================================
# 🚀 Pipeline & API Interactions
# ============================================================================

train: ## Déclenche un entraînement manuel via l'API
	@echo "Déclenchement de l'entraînement..."
	@curl -X POST http://localhost:8080/training/ -H "Content-Type: application/json" -d '{"force": true}'

predict: ## Teste une prédiction pour l'utilisateur 1
	@echo "Demande de recommandation pour User 1..."
	@curl -X POST http://localhost:8080/predict/ -H "Content-Type: application/json" -d '{"user_id": 1, "n_recommendations": 5}'

generate-data: ## Génère 100 nouveaux votes aléatoires
	@echo "Génération de données..."
	@curl -X POST "http://localhost:8080/generate-ratings/?batch_size=100"

stats: ## Affiche les statistiques de la base de données
	@curl -s http://localhost:8080/stats | python -m json.tool

# ============================================================================
# 🎨 Streamlit Specific
# ============================================================================

streamlit-rebuild: ## Reconstruit et redémarre uniquement le conteneur Streamlit
	docker compose up -d --build streamlit
