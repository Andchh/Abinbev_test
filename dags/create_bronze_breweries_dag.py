from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime
import requests
import json
import os

def fetch_and_save_raw_data(**context):
    url = "https://api.openbrewerydb.org/v1/breweries"
    all_data = []
    page = 1

    while True:
        response = requests.get(url, params={"per_page": 50, "page": page})
        data = response.json()

        if response.status_code != 200:
            print(f"Erro na requisição da página {page}: status {response.status_code}")
            break

        if not data:
            print("Nenhum dado retornado. Fim da paginação.")
            break

        all_data.extend(data)
        print(f"Página {page} coletada com {len(data)} registros.")
        page += 1

    # Caminho onde os dados serão salvos
    output_dir = "/opt/airflow/datalake/bronze"
    os.makedirs(output_dir, exist_ok=True)

    # Nome do arquivo
    file_path = os.path.join(output_dir, f"breweries_raw.json")

    # Salvar o JSON bruto
    with open(file_path, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"Dados salvos em {file_path}")

default_args = {
    "start_date": datetime(2025, 1, 1),
    "retries": 3,
    "email": ["seu_email@example.com"],
    "email_on_failure": True,
    "email_on_retry": False,
}

with DAG(
    dag_id="create_bronze_breweries",
    schedule="@daily",
    default_args=default_args,
    catchup=False
) as dag:
    
    start = EmptyOperator(task_id='start')

    fetch_raw_data = PythonOperator(
        task_id="fetch_and_save_raw_brewery_data",
        python_callable=fetch_and_save_raw_data
    )

    end = EmptyOperator(task_id='end')
    
    start >> fetch_raw_data >> end