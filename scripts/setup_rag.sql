
CREATE OR REPLACE MODEL `met_data.gemini_model`
  REMOTE WITH CONNECTION `us.met_data_conn`
  OPTIONS (ENDPOINT = 'gemini-2.0-flash');

CREATE OR REPLACE MODEL `met_data.embeddings_model`
  REMOTE WITH CONNECTION `us.met_data_conn`
  OPTIONS (ENDPOINT = 'text-embedding-005');

# Create Tables

# create ai_ouputs table

CREATE OR REPLACE TABLE `met_data.fashion_ai_outputs` AS
SELECT
  ml_generate_text_result['candidates'][0]['content'] AS generated_text,
  * EXCEPT (ml_generate_text_result)
FROM
  ML.GENERATE_TEXT(
    MODEL `met_data.gemini_model`,
    (
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
        images.original_image_url,
      FROM (
        SELECT
          *,
          ROW_NUMBER() OVER (PARTITION BY original_image_url ORDER BY object_id) AS rn
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
      -- LIMIT 5
    ),
    STRUCT(
      1.0 AS temperature,
      500 AS max_output_tokens
    )
  );


# create ai_ouputs formatted table

CREATE OR REPLACE TABLE `met_data.fashion_ai_outputs_formatted` AS
SELECT
  * EXCEPT (generated_text),
  JSON_VALUE(generated_text, '$.parts[0].text') AS generated_text
FROM
  `met_data.fashion_ai_outputs`;

# Setup RAG

# embeddings
CREATE OR REPLACE TABLE `met_data.fashion_ai_outputs_embeddings` AS
SELECT * FROM ML.GENERATE_TEXT_EMBEDDING(
  MODEL `met_data.embeddings_model`,(
      SELECT * EXCEPT(generated_text), generated_text AS content
      FROM `met_data.fashion_ai_outputs_formatted`
      WHERE gcs_url IS NOT NULL
    )
);

# create vector index
CREATE OR REPLACE VECTOR INDEX met_data_index ON met_data.fashion_ai_outputs_embeddings(text_embedding)
OPTIONS(index_type = 'IVF', distance_type = 'COSINE',
ivf_options = '{"num_lists": 10}');

 SELECT table_name, index_name, index_status, coverage_percentage, last_refresh_time,disable_reason FROM `met_data.INFORMATION_SCHEMA.VECTOR_INDEXES`
WHERE table_name = "fashion_ai_outputs_embeddings";



     
