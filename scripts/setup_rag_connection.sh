#!/bin/bash

# Exit on error
set -e

# Configuration variables
PROJECT_ID="<YOUR_PROJECT_ID>"
LOCATION="US"
DATASET_NAME="met_data"
CONNECTION_NAME="met_data_conn"
DESCRIPTION="Met data for the ADK hackathon"

# Create BigQuery dataset
echo "Creating BigQuery dataset: $DATASET_NAME..."
bq --location=${LOCATION} mk -d \
  --description "${DESCRIPTION}" \
  ${DATASET_NAME}

# Create BigQuery connection (Cloud Resource)
echo "Creating BigQuery connection: $CONNECTION_NAME..."
bq mk --connection \
  --location=${LOCATION} \
  --project_id=${PROJECT_ID} \
  --connection_type=CLOUD_RESOURCE \
  ${CONNECTION_NAME}

# Show the created connection
echo "Showing connection details:"
bq show --connection ${PROJECT_ID}.${LOCATION,,}.${CONNECTION_NAME}
