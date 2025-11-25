from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.sensors.http_sensor import HttpSensor
from datetime import datetime, timedelta
import json

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'movie_reco_training_pipeline',
    default_args=default_args,
    description='Pipeline d\'entraînement du modèle de recommandation de films',
    schedule_interval='0 2 * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['mlops', 'reco'],
) as dag:

    check_api_health = HttpSensor(
        task_id='check_api_health',
        http_conn_id='api_connection',
        endpoint='/health',
        method='GET',
        response_check=lambda response: response.status_code == 200,
        poke_interval=30,
        timeout=120,
    )

    trigger_training = SimpleHttpOperator(
        task_id='trigger_training',
        http_conn_id='api_connection',
        endpoint='/training/',
        method='POST',
        data=json.dumps({"force": True}),
        headers={"Content-Type": "application/json"},
        response_check=lambda response: response.status_code == 200,
        log_response=True
    )
    
    check_api_health >> trigger_training

