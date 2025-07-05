import os
import subprocess
import time

from dotenv import load_dotenv, find_dotenv
from google.cloud import bigquery
from google.cloud import bigquery_connection_v1 as bq_connection
from google.cloud.exceptions import NotFound
from rich import print
from rich.progress import Progress

# Load environment variables
load_dotenv(find_dotenv())

# Configuration
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
project_location = os.getenv("GOOGLE_CLOUD_LOCATION")
bigquery_region = os.getenv("BIGQUERY_REGION")
bigquery_dataset_id = os.getenv("BIGQUERY_DATASET_ID")
bigquery_connection_id = os.getenv("BIGQUERY_CONNECTION_ID")
bigquery_embedding_model_id = os.getenv("BIGQUERY_EMBEDDINGS_MODEL_ID")
bigquery_embedding_model = os.getenv("BIGQUERY_EMBEDDINGS_MODEL")
bigquery_caption_model_id = os.getenv("BIGQUERY_CAPTIONING_MODEL_ID")
bigquery_caption_model = os.getenv("BIGQUERY_CAPTIONING_MODEL")
bigquery_table_id = os.getenv("BIGQUERY_TABLE_ID")
bigquery_vector_index_id = os.getenv("BIGQUERY_VECTOR_INDEX_ID")

# Initialize BigQuery client
client = bigquery.Client(project=project_id)

def run_bq_query(sql: str):
    """
    Executes a SQL query using the BigQuery client and returns the result.
    """
    query_job = client.query(sql)
    result = query_job.result()
    print(f"[green]Executed query job:[/green] {query_job.job_id}")
    return result

def create_bigquery_dataset(dataset_id: str):
    """
    Creates a BigQuery dataset if it does not already exist.
    """
    dataset_ref = f"{project_id}.{dataset_id}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = bigquery_region
    try:
        client.get_dataset(dataset)
        print(f"[yellow]Dataset {dataset_ref} already exists[/yellow]")
    except NotFound:
        client.create_dataset(dataset, timeout=30)
        print(f"[green]Created dataset {dataset_ref}[/green]")

def create_bigquery_connection(connection_id: str) -> str:
    """
    Creates a new BigQuery connection if one does not exist.
    """
    conn_client = bq_connection.ConnectionServiceClient()
    parent = f"projects/{project_id}/locations/{bigquery_region}"
    conn_path = f"{parent}/connections/{connection_id}"

    try:
        request = conn_client.get_connection(name=conn_path)
        return f"serviceAccount:{request.cloud_resource.service_account_id}"
    except Exception:
        connection = bq_connection.types.Connection(
            friendly_name=connection_id,
            cloud_resource=bq_connection.CloudResourceProperties()
        )
        response = conn_client.create_connection(
            parent=parent,
            connection_id=connection_id,
            connection=connection
        )
        return f"serviceAccount:{response.cloud_resource.service_account_id}"

def setup_project_permissions(project_id: str, conn_service_account: str):
    """
    Grants required IAM roles and enables the BigQuery Connection API.
    """
    roles = [
        'roles/serviceusage.serviceUsageConsumer',
        'roles/bigquery.connectionUser',
        'roles/aiplatform.user'
    ]

    for role in roles:
        cmd = [
            "gcloud", "projects", "add-iam-policy-binding", project_id,
            "--condition=None", "--no-user-output-enabled",
            f"--member={conn_service_account}", f"--role={role}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[red]Failed to assign {role}[/red]: {result.stderr.strip()}")
        else:
            print(f"[green]Granted {role}[/green]")

    print("[cyan]Enabling BigQuery Connection API...[/cyan]")
    subprocess.run(["gcloud", "services", "enable", "bigqueryconnection.googleapis.com"],
                   capture_output=True, text=True)
    print("[yellow]Waiting 60 seconds for IAM propagation...[/yellow]")
    time.sleep(60)

def create_model(connection_id: str, model_id: str, model_endpoint: str):
    """
    Creates or replaces a remote BigQuery ML model backed by Vertex AI endpoint.
    """
    sql = f"""
    CREATE OR REPLACE MODEL `{project_id}.{bigquery_dataset_id}.{model_id}`
    REMOTE WITH CONNECTION `{project_id}.{bigquery_region}.{connection_id}`
    OPTIONS (ENDPOINT = '{model_endpoint}');
    """
    return run_bq_query(sql)

def create_gemini_captions_table():
    """
    Creates a BigQuery table using `ML.GENERATE_TEXT` to produce captions from metadata.
    """
    sql = f"""
    CREATE OR REPLACE TABLE `{bigquery_dataset_id}.{bigquery_table_id}` AS
    SELECT
      ml_generate_text_result['candidates'][0]['content'] AS generated_text,
      * EXCEPT (ml_generate_text_result)
    FROM
      ML.GENERATE_TEXT(
        MODEL `{bigquery_dataset_id}.{bigquery_caption_model_id}`,(
         SELECT
        objects.object_id,
        objects.object_name,
        objects.object_begin_date,
        objects.object_end_date,
        FORMAT(
          '''Describe the dress in the image in detail, make sure to incorporate the following metadata:
          Additionally, incorporate this metadata:
          - Culture: %s
          - Period: %s
          - Artist: %s
          - Medium: %s
          - Date: %s - %s

            Structure your response using the following format and section headings:
              Overall Impression:
              Fabric and Print
              Color pallette 
              Bodice
              Sleeves
              Skirt    

            Do not include introductory phrases like “Here is the description” or “This image shows.”
            Do not add bullet points or formatting beyond the category headers.
            Output should be in plain text, written in complete sentences with a fashion-specific, fluent tone.

          Image URL: %s''',
          IFNULL(objects.culture, '(not specified)'),
          IFNULL(objects.period, '(not specified)'),
          IFNULL(objects.artist_display_name, '(not specified)'),
          IFNULL(objects.medium, '(not specified)'),
          IFNULL(CAST(objects.object_begin_date AS STRING), '(not specified)'),
          IFNULL(CAST(objects.object_end_date AS STRING), '(not specified)'),
          images.gcs_url
        ) AS prompt,
        images.gcs_url,
        images.original_image_url
      FROM (
        SELECT 
          *,
          ROW_NUMBER() OVER (PARTITION BY object_id ORDER BY gcs_url) AS rn
        FROM 
          `bigquery-public-data.the_met.images`
        WHERE 
          original_image_url IS NOT NULL
          AND gcs_url IS NOT NULL
      ) AS images
      JOIN 
        `bigquery-public-data.the_met.objects` AS objects
      ON 
        images.object_id = objects.object_id
      WHERE 
        images.rn = 1
        AND objects.department = "Costume Institute"
        AND objects.is_public_domain = TRUE
        AND (
          LOWER(objects.object_name) LIKE "%dress%"
          OR LOWER(objects.object_name) LIKE "%evening dress%"
        )
      ORDER BY 
        objects.title
    ),
    STRUCT(
      1.0 AS temperature,
      500 AS max_output_tokens
    )
  );
    """
    return run_bq_query(sql)

def create_gemini_formatted_captions_table():
    """
    Creates a new table that extracts plain text from Gemini's JSON-formatted captions.
    """
    sql = f"""
    CREATE OR REPLACE TABLE `{bigquery_dataset_id}.{bigquery_table_id}_formatted` AS
    SELECT
      * EXCEPT (generated_text),
      JSON_VALUE(generated_text, '$.parts[0].text') AS generated_text
    FROM `{bigquery_dataset_id}.{bigquery_table_id}`;
    """
    return run_bq_query(sql)

def create_fashion_embeddings_table():
    """
    Generates text embeddings using `ML.GENERATE_TEXT_EMBEDDING` and stores the result in BigQuery.
    """
    sql = f"""
    CREATE OR REPLACE TABLE `{bigquery_dataset_id}.{bigquery_table_id}_embeddings` AS
    SELECT * FROM ML.GENERATE_TEXT_EMBEDDING(
      MODEL `{bigquery_dataset_id}.{bigquery_embedding_model_id}`,
      (
        SELECT * EXCEPT(generated_text), generated_text AS content
        FROM `{bigquery_dataset_id}.{bigquery_table_id}_formatted`
        WHERE gcs_url IS NOT NULL
      )
    );
    """
    return run_bq_query(sql)

def create_vector_index(num_lists: int = 10):
    """
    Creates a vector index on the text embeddings using IVF and COSINE distance.
    """
    sql = f"""
    CREATE OR REPLACE VECTOR INDEX `{bigquery_dataset_id}.{bigquery_vector_index_id}`
    ON {bigquery_dataset_id}.{bigquery_table_id}_embeddings(text_embedding)
    OPTIONS (
        index_type = 'IVF',
        distance_type = 'COSINE',
        ivf_options = '{{"num_lists": {num_lists}}}'
    );
    """
    return run_bq_query(sql)

def main():
    with Progress() as progress:
        task = progress.add_task("[bold green]Setting up RAG pipeline...", total=8)

        create_bigquery_dataset(bigquery_dataset_id)
        progress.advance(task)

        conn_service_account = create_bigquery_connection(bigquery_connection_id)
        progress.advance(task)

        setup_project_permissions(project_id, conn_service_account)
        progress.advance(task)

        create_model(bigquery_connection_id, bigquery_embedding_model_id, bigquery_embedding_model)
        progress.advance(task)

        create_model(bigquery_connection_id, bigquery_caption_model_id, bigquery_caption_model)
        progress.advance(task)

        create_gemini_captions_table()
        progress.advance(task)

        create_gemini_formatted_captions_table()
        progress.advance(task)

        create_fashion_embeddings_table()
        # create_vector_index(num_lists=10)
        progress.advance(task)

    print("\n[bold cyan]\u2705 RAG setup complete.[/bold cyan]")