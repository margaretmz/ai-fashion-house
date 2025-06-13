import urllib
from typing import Optional

import numpy as np
import pandas as pd
from google.cloud import bigquery
from matplotlib import pyplot as plt
import PIL.Image
import urllib.request

# Configuration
PROJECT_ID = "build-with-ai-project"
DATASET_ID = "met_data"
EMBEDDINGS_TABLE_ID = "fashion_ai_outputs_embeddings"
REGION = "US"
CONN_NAME = "met_data_conn"
EMBEDDINGS_MODEL_ID = "embeddings_model"
EMBEDDINGS_MODEL = "text-embedding-005"

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID)


def run_bq_query(sql: str) -> bigquery.table.RowIterator:
    """
    Executes a BigQuery SQL query and returns the result.

    Args:
        sql (str): SQL query to run.

    Returns:
        RowIterator: Result of the query.

    Raises:
        Exception: If query execution fails.
    """
    try:
        query_job = client.query(sql)
        result = query_job.result()
        print(f"[✅] Job ID: {query_job.job_id} | Status: {query_job.state}")
        return result
    except Exception as e:
        raise RuntimeError(f"[❌] Query failed: {e}")


def create_model(model_id: str, endpoint: str) -> None:
    """
    Creates or replaces a remote BigQuery ML model with an embedding endpoint.

    Args:
        model_id (str): BigQuery ML model ID to create.
        endpoint (str): Remote model endpoint ID (e.g., 'text-embedding-005').
    """
    sql = f"""
    CREATE OR REPLACE MODEL `{PROJECT_ID}.{DATASET_ID}.{model_id}`
    REMOTE WITH CONNECTION `{PROJECT_ID}.{REGION}.{CONN_NAME}`
    OPTIONS (ENDPOINT = '{endpoint}');
    """
    run_bq_query(sql)
    print(f"[🧠] Model `{model_id}` created with endpoint `{endpoint}`.")


def query_rag(
        user_query: str,
        top_k: int = 5,
        search_fraction: float = 0.01
) -> Optional[pd.DataFrame]:
    """
    Executes a vector similarity search against the embeddings table.

    Args:
        user_query (str): Text query to embed and search for.
        top_k (int): Number of top matches to retrieve.
        search_fraction (float): Fraction of lists to search.

    Returns:
        DataFrame: Top K most similar entries from the embedding table.
    """
    sql = f"""
    SELECT query.query,
    distance,
    base.content,
    base.original_image_url
    FROM VECTOR_SEARCH(
      TABLE `{PROJECT_ID}.{DATASET_ID}.{EMBEDDINGS_TABLE_ID}`,
      'text_embedding',
      (
        SELECT
          text_embedding,
          content AS query
        FROM ML.GENERATE_TEXT_EMBEDDING(
          MODEL `{PROJECT_ID}.{DATASET_ID}.{EMBEDDINGS_MODEL_ID}`,
          (SELECT '{user_query}' AS content)
        )
      ),
      top_k => {top_k},
      OPTIONS => '{{"fraction_lists_to_search": {search_fraction}}}'
    );
    """
    results = run_bq_query(sql).to_dataframe()
    return results


if __name__ == '__main__':

    # Run retrieval-augmented generation query
    results = query_rag("Vibrant still life features a collection of boldly colored, geometric-shaped objects, including a bright yellow pitcher, a red and blue", top_k=5, search_fraction=0.01)
    results.to_csv("results.csv", index=False)

    # visualize images
    n_cols = 2
    n_rows = (len(results) + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(10, 5 * n_rows))
    # Flatten axes for uniform indexing
    axes = axes.flatten() if n_rows > 1 else axes
    for i, (index, row) in enumerate(results.iterrows()):
        ax = axes[i]
        try:
            with urllib.request.urlopen(row['original_image_url']) as url:
                image = PIL.Image.open(url)
                ax.imshow(np.array(image))
                ax.set_title(f"Distance: {row['distance']:.4f}")
        except Exception as e:
            ax.set_title("Image not available")
        ax.axis('off')

    # Hide any unused axes
    for j in range(i + 1, len(axes)):
        axes[j].axis('off')

    plt.tight_layout()
    plt.show()