import os
import urllib
from typing import Optional

import numpy as np
import pandas as pd
from google.cloud import bigquery
from matplotlib import pyplot as plt
import PIL.Image
import urllib.request
from dotenv import load_dotenv, find_dotenv
from google import genai

# Load environment variables
load_dotenv(find_dotenv())

# Configuration
PROJECT_ID = "build-with-ai-project"
DATASET_ID = "met_data"
EMBEDDINGS_TABLE_ID = "fashion_ai_outputs_embeddings"
REGION = "US"
CONN_NAME = "met_data_conn"
EMBEDDINGS_MODEL_ID = "embeddings_model"
EMBEDDINGS_MODEL = "text-embedding-005"

# Initialize BigQuery client
bigquery_client = bigquery.Client(project=PROJECT_ID)
gemini_client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


def get_user_query_enhancement_prompt(user_input: str) -> str:
    """
    Creates a prompt enhancer for user queries to improve search results.

    Returns:
        str: Prompt enhancer string.
    """
    prompt = f"""
        You are a fashion assistant that helps refine vague or casual user input into precise, vivid fashion descriptions suitable for matching against historical fashion items.
        
        The user provided the following input:
        "{user_input}"
        
        Your task is to:
        - Generate a **single, vivid, and fluent fashion description**.
        - Use fashion-specific vocabulary.
        - Describe visual motifs, color palette, garment structure, and silhouette.
        - DO NOT include phrases like "Here is the description" or "This image shows".
        - DO NOT format output as JSON or list—just return the **raw descriptive text**.
        
        The output should closely resemble fashion captions like:
        "A floor-length evening gown in deep emerald velvet with delicate floral embroidery and a fitted bodice, flaring into a bell-shaped skirt characteristic of the mid-19th century."
        
        Now, based on the user's input, generate the refined description:
        """

    return gemini_client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=prompt,
    ).text.strip()



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
        query_job = bigquery_client.query(sql)
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

    tables = bigquery_client.list_tables("bigquery-public-data.the_met")  # Make an API request.
    for table in tables:
        print("{}.{}.{}".format(table.project, table.dataset_id, table.table_id))

    # Run retrieval-augmented generation query
    # query  = get_user_query_enhancement_prompt("I'm looking for a Victorian dress with lace and red accents.")
    # query = get_user_query_enhancement_prompt("I want something romantic with lace from the 1800s")
    query = get_user_query_enhancement_prompt("Something extravagant for a royal ball in the 1800s.")

    print(query)

    results = query_rag(query, top_k=5, search_fraction=0.01)
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