from airflow.models import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.sensors.external_task import ExternalTaskSensor
from datetime import datetime, timedelta
import os

with DAG(
    dag_id='create_silver_breweries',
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["spark", "silver", "breweries"],
    default_args={
        'retries': 2,
        'retry_delay': timedelta(minutes=1),
        'owner': 'airflow'
    }
) as dag:
    
    start = EmptyOperator(task_id='start')

    # Sensor para aguardar a conclusão da DAG da camada silver
    wait_for_bronze = ExternalTaskSensor(
        task_id='wait_for_bronze',
        external_dag_id='create_bronze_brewery',
        external_task_id='end',  # Espera pela tarefa 'end' da DAG silver
        timeout=600,  # Timeout de 10 minutos
        poke_interval=60,  # Verifica a cada 1 minuto
        mode='reschedule',  # Libera o worker durante a espera
        allowed_states=['success'],  # Só prossegue se a DAG bronze for bem-sucedida
        failed_states=['failed', 'skipped', 'upstream_failed'],
        execution_delta=timedelta(minutes=0) 
    )

    #job silver
    spark_job = DockerOperator(
        task_id='create_silver_breweries',
        image='spark-air',
        command='spark-submit --master local[*] --driver-memory 1g --executor-memory 1g /opt/airflow/spark/app/create_silver_breweries.py',
        docker_url='tcp://docker-proxy:2375',
        network_mode='brewer_default',
        mounts=[
            {
                "source": "brewer_spark-app-scripts",
                "target": "/opt/airflow/spark/app",
                "type": "volume"
            },
            {
                "source": "brewer_datalake-volume",
                "target": "/opt/airflow/datalake",
                "type": "volume"
            }
        ],
        auto_remove="success",
        tmp_dir="/tmp",
        mount_tmp_dir=False
    )

    end = EmptyOperator(task_id='end')

    start >> spark_job >> end    