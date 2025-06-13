-- # Filter data

-- SELECT COUNT(*) FROM `bigquery-public-data.the_met.objects` where department = "Costume Institute" and is_public_domain = TRUE;


-- SELECT 
--   images.gcs_url,
--   images.original_image_url,
--   objects.department,
--   objects.title
-- FROM (
--   SELECT 
--     *,
--     ROW_NUMBER() OVER (PARTITION BY original_image_url ORDER BY object_id) AS rn
--   FROM 
--     `bigquery-public-data.the_met.images`
--   WHERE 
--     original_image_url IS NOT NULL
--     AND gcs_url IS NOT NULL
-- ) AS images
-- JOIN 
--   `bigquery-public-data.the_met.objects` AS objects
-- ON 
--   images.object_id = objects.object_id
-- WHERE 
--   images.rn = 1
--   AND objects.department = "Costume Institute"
--   AND objects.is_public_domain = TRUE
-- ORDER BY 
--   objects.title
-- LIMIT 100;


-- SELECT 
--   COUNT(*) AS total_unique_images
-- FROM (
--   SELECT 
--     images.original_image_url,
--     ROW_NUMBER() OVER (PARTITION BY images.original_image_url ORDER BY images.object_id) AS rn
--   FROM 
--     `bigquery-public-data.the_met.images` AS images
--   JOIN 
--     `bigquery-public-data.the_met.objects` AS objects
--   ON 
--     images.object_id = objects.object_id
--   WHERE 
--     images.original_image_url IS NOT NULL
--     AND images.gcs_url IS NOT NULL
--     AND objects.department = "Costume Institute"
--     AND objects.is_public_domain = TRUE
-- ) AS deduped
-- WHERE rn = 1;


# Generate Captions

CREATE OR REPLACE MODEL `met_data.gemini_model`
  REMOTE WITH CONNECTION `us.met_data_conn`
  OPTIONS (ENDPOINT = 'gemini-2.0-flash');

CREATE OR REPLACE MODEL `met_data.embeddings_model`
  REMOTE WITH CONNECTION `us.met_data_conn`
  OPTIONS (ENDPOINT = 'text-embedding-005');



SELECT
  ml_generate_text_result['candidates'][0]['content'] AS generated_text,
  * EXCEPT (ml_generate_text_result)
FROM
  ML.GENERATE_TEXT(
    MODEL `met_data.gemini_model`,(
      SELECT
        CONCAT('Describe the visual motifs, color palette, garment structure, and how this piece could influence your next collection. Image URL: ', gcs_url) AS prompt,
        *
      FROM
        `bigquery-public-data.the_met.images`
      LIMIT 5
    ),
    STRUCT(
      0.2 AS temperature,
      500 AS max_output_tokens));


DROP TABLE IF EXISTS `met_data.fashion_ai_outputs`;
CREATE OR REPLACE TABLE `met_data.fashion_ai_outputs` AS
SELECT
  ml_generate_text_result['candidates'][0]['content'] AS generated_text,
  * EXCEPT (ml_generate_text_result)
FROM
  ML.GENERATE_TEXT(
    MODEL `met_data.gemini_model`,
    (
      SELECT
        CONCAT(
          'Caption in  single sentence the following image, highlighthing the color, style, shapes etc. Image URL: ',
          images.gcs_url
        ) AS prompt,
        images.gcs_url,
        images.original_image_url,
        objects.title,
        objects.department
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
      ORDER BY 
        objects.title
      -- LIMIT 5
    ),
    STRUCT(
      0.2 AS temperature,
      500 AS max_output_tokens
    )
  );

# Format

DROP TABLE IF EXISTS `met_data.fashion_ai_outputs_formatted`;
CREATE OR REPLACE TABLE `met_data.fashion_ai_outputs_formatted` AS
SELECT
  title,
  gcs_url,
  original_image_url,
  JSON_VALUE(generated_text, '$.parts[0].text') AS generated_text
FROM
  `met_data.fashion_ai_outputs`;

# RAG 

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



     
