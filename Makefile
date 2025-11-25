.PHONY: all build up down logs volumes dvc_repro restart_pipeline train_and_predict

# Créer les volumes Docker
volumes:
	docker volume create minio_data || true
	docker volume create mlflow_db || true

# Construire tous les conteneurs
build:
	docker compose build

# Lancer tous les conteneurs
up: 
	docker compose up

# Arrêter tous les conteneurs
down:
	docker compose down

# Voir les logs en temps réel
logs:
	docker compose logs -f

# Reproduire les stages DVC dans le conteneur pipeline
restart_pipeline:
	docker compose run --rm -e PYTHONPATH=/workspace/src pipeline dvc repro -f

# Lancer uniquement le training et la prédiction

train_and_predict:
	docker compose run --rm -e PYTHONPATH=/workspace/src pipeline \
		dvc repro -f stage04_train_model stage05_predict_model
