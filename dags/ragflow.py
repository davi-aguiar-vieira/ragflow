from datetime import datetime
import json
import os
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from minio import Minio
from ragflow.agent_api.client import RagflowClient
from ragflow.agent_api.config import AGENT_EXPLANATOR_ID

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'your-minio-endpoint')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'your-access-key')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'your-secret-key')
SOURCE_BUCKET = os.getenv('MINIO_SOURCE_BUCKET', 'your-bucket-name')
DEST_BUCKET = os.getenv('MINIO_DEST_BUCKET', 'fake-news-explanations')

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

def fetch_files_modified_today(bucket_name, **context):
    today = datetime.date.today()
    files = []
    for obj in minio_client.list_objects(bucket_name, recursive=True):
        if obj.last_modified.date() == today:
            files.append(obj.object_name)
    # Salva na XCom para o próximo task
    context['ti'].xcom_push(key='today_files', value=files)
    return files

def process_and_save_fakes(bucket_name, dest_bucket, **context):
    files = context['ti'].xcom_pull(key='today_files', task_ids='fetch_files')
    if not files:
        return "Nenhum arquivo para processar hoje."
    client = RagflowClient()
    explicador = RagflowClient(agent_id=AGENT_EXPLANATOR_ID)
    results = []
    for file_name in files:
        try:
            response = minio_client.get_object(bucket_name, file_name)
            data = json.load(response)
            body = data.get('body')
            url = data.get('url')
            if not body or not url:
                continue
            session_id = client.start_session()
            analysis_response = client.analyze_materia(body, session_id)
            answer = analysis_response.get('data', {}).get('answer', '')
            if 'FAKE' in answer.upper():
                explicador_session = explicador.start_session()
                detalhamento = explicador.analyze_materia(body, explicador_session)
                explicacao = detalhamento.get('data', {}).get('answer', '')
                # Salva no bucket de destino
                output = {
                    'url': url,
                    'explanation': explicacao,
                    'analyzed_at': datetime.isoformat()
                }
                output_name = f"{os.path.splitext(os.path.basename(file_name))[0]}_fake_explanation.json"
                minio_client.put_object(
                    dest_bucket,
                    output_name,
                    data=bytes(json.dumps(output), 'utf-8'),
                    length=len(json.dumps(output)),
                    content_type='application/json'
                )
                results.append(output_name)
        except Exception as e:
            print(f"Erro ao processar {file_name}: {e}")
    return f"Arquivos processados e salvos: {results}"

with DAG(
    'minio_to_ragflow_dag',
    schedule_interval='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False
) as dag:
    fetch_files_task = PythonOperator(
        task_id='fetch_files',
        python_callable=fetch_files_modified_today,
        op_kwargs={'bucket_name': SOURCE_BUCKET},
        provide_context=True,
    )

    process_files_task = PythonOperator(
        task_id='process_and_save_fakes',
        python_callable=process_and_save_fakes,
        op_kwargs={'bucket_name': SOURCE_BUCKET, 'dest_bucket': DEST_BUCKET},
        provide_context=True,
    )

    fetch_files_task >> process_files_task